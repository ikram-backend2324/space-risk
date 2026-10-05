"""
Deterministic SPACE RISK forecasting engine.

Projects each region's satellite-derived baseline indices forward using
per-hazard climate trends. It is used on its own when no OpenRouter key is
configured (or the AI call fails), and to build the per-hazard time series
that the AI forecast is interpolated onto.
"""
import hashlib
import math
from datetime import date

from .hazards import HAZARDS, LEVEL_LABELS, level_for

RECOMMENDATIONS = {
    "seismic": [
        ("Binolarni seysmik audit qilish", "Maktab, shifoxona va koʻp qavatli uylarni 8–9 ballik zilzilaga chidamlilik boʻyicha tekshirish va kuchaytirish dasturini boshlash.", "high"),
        ("InSAR monitoring", "Sentinel-1 radar maʼlumotlari asosida yer qobigʻi deformatsiyasini har 6 kunda kuzatish.", "medium"),
    ],
    "flood": [
        ("Sel erta ogohlantirish tizimi", "Togʻ soylarida avtomatik datchiklar va GPM yogʻin prognozlarini birlashtirib, aholiga SMS-ogohlantirish yuborish.", "high"),
        ("Suv omborlari xavfsizligi", "Toʻgʻonlar holatini sunʼiy yoʻldosh va dron orqali muntazam tekshirish.", "medium"),
    ],
    "drought": [
        ("Tomchilatib sugʻorish", "Qishloq xoʻjaligida suvni tejovchi texnologiyalarni subsidiyalash va 30% gacha suv tejash.", "high"),
        ("NDVI asosida hosil monitoringi", "MODIS/Sentinel-2 vegetatsiya indekslari bilan qurgʻoqchilikni 4–6 hafta oldin aniqlash.", "medium"),
    ],
    "heatwave": [
        ("Shahar issiqlik orollarini kamaytirish", "Yashil zonalar, salqin tomlar va soya beruvchi infratuzilmani kengaytirish.", "high"),
        ("Issiqlik harakat rejasi", "+40°C dan yuqori kunlarda aholini ogohlantirish va salqinlash markazlarini ochish.", "medium"),
    ],
    "landslide": [
        ("Koʻchki xaritalash", "DEM va InSAR maʼlumotlari asosida xavfli yonbagʻirlarni aniqlab, qurilishni cheklash.", "high"),
        ("Yonbagʻirlarni mustahkamlash", "Daraxt ekish va drenaj tizimlari orqali surilish xavfini kamaytirish.", "medium"),
    ],
    "dust": [
        ("Orol tubini oʻrmonlashtirish", "Saksovul va boshqa choʻl oʻsimliklarini ekish orqali tuzli chang manbalarini barqarorlashtirish.", "high"),
        ("Chang boʻroni prognozi", "Sentinel-5P va MODIS AOD maʼlumotlari bilan 48 soatlik chang prognozi xizmatini yoʻlga qoʻyish.", "medium"),
    ],
    "water": [
        ("Suv resurslarini raqamli boshqarish", "GRACE-FO yer osti suv maʼlumotlari asosida kanallar va quduqlarda smart-hisoblagichlar joriy etish.", "high"),
        ("Kanallarni betonlash", "Sugʻorish tarmogʻidagi filtratsiya yoʻqotishlarini kamaytirish.", "medium"),
    ],
    "air": [
        ("Emissiyalarni nazorat qilish", "Sanoat korxonalarida uzluksiz emissiya monitoringi va Sentinel-5P NO₂ xaritalari bilan solishtirish.", "high"),
        ("Toza transport", "Elektr jamoat transporti va velo-infratuzilmani kengaytirish.", "low"),
    ],
    "desertification": [
        ("Yer degradatsiyasini toʻxtatish", "Shoʻrlangan yerlarni yuvish, almashlab ekish va choʻlga chidamli ekinlarni joriy etish.", "high"),
        ("Landsat 40 yillik tahlil", "Yer qoplami oʻzgarishini arxiv tasvirlari orqali baholab, ustuvor hududlarni belgilash.", "low"),
    ],
}


def _jitter(*parts, spread=3.0):
    digest = hashlib.sha256("|".join(map(str, parts)).encode()).digest()
    return (digest[0] / 255 * 2 - 1) * spread


def _clamp(v, lo=0.0, hi=100.0):
    return max(lo, min(hi, v))


def project(baseline, code, years, slug=""):
    """Projected 0..100 index for one hazard after ``years``."""
    meta = HAZARDS[code]
    if code == "seismic":
        # Hazard is ~constant, but the chance of a damaging event within the window grows.
        value = baseline * (0.82 + 0.22 * (1 - math.exp(-years / 8)))
    else:
        # Climate trends accelerate slightly where the baseline is already high,
        # and approach (never hit) the 100 ceiling asymptotically.
        increment = meta["trend"] * years * (0.7 + baseline / 160)
        headroom = max(100 - baseline, 1)
        value = 100 - headroom * math.exp(-increment / headroom)
    return round(_clamp(value + _jitter(slug, code, years) * min(1, years / 3), 0, 99), 1)


def composite(scores):
    vals = list(scores.values())
    if not vals:
        return 0.0
    top = sorted(vals, reverse=True)[:3]
    return round(0.6 * sum(top) / len(top) + 0.4 * sum(vals) / len(vals), 1)


def timeline_points(horizon):
    """(label, years-from-now) pairs for the chart."""
    start = date.today().year
    if horizon == 1:
        return [(f"{start}", 0), ("+3 oy", 0.25), ("+6 oy", 0.5), ("+9 oy", 0.75), (f"{start + 1}", 1)]
    steps = 5 if horizon <= 10 else 6
    points = []
    for i in range(steps):
        years = horizon * i / (steps - 1)
        years = int(years) if years == int(years) else years  # keep jitter keys stable ("10", not "10.0")
        points.append((str(start + round(years)), years))
    return points


def build_timeline(region, hazards, horizon, final_scores=None, overall_path=None):
    """Per-hazard series from today's baseline to the final scores (interpolated)."""
    points = timeline_points(horizon)
    out = []
    for idx, (label, years) in enumerate(points):
        hz = {}
        for code in hazards:
            base = region.baseline.get(code, 30)
            if final_scores and code in final_scores:
                # Ease from today's baseline to the AI target score.
                frac = years / max(horizon, 1)
                frac = frac * (0.6 + 0.4 * frac)
                hz[code] = round(_clamp(base + (final_scores[code] - base) * frac), 1)
            else:
                hz[code] = project(base, code, years, region.slug)
        overall = composite(hz)
        if overall_path and idx < len(overall_path):
            overall = round(_clamp(float(overall_path[idx])), 1)
        out.append({"label": label, "overall": overall, "hazards": hz})
    return out


def forecast(region, hazards, horizon, notes=""):
    hazards = [h for h in hazards if h in HAZARDS] or list(HAZARDS)
    scores = {code: project(region.baseline.get(code, 30), code, horizon, region.slug) for code in hazards}
    overall = composite(scores)
    level = level_for(overall)
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    top = ranked[:3]
    target = date.today().year + horizon

    top_txt = ", ".join(f"{HAZARDS[c]['label'].lower()} ({s:.0f})" for c, s in top)
    rising = [c for c, _ in ranked if HAZARDS[c]["trend"] >= 0.8][:2]
    summary = (
        f"{region.name} uchun {target}-yilgacha boʻlgan umumiy xavf indeksi {overall:.0f}/100 — "
        f"“{LEVEL_LABELS[level]}” darajada. Eng kuchli tahdidlar: {top_txt}. "
    )
    if rising:
        summary += (
            "Iqlim oʻzgarishi sababli " + " va ".join(HAZARDS[c]["label"].lower() for c in rising)
            + " xavfi har yili ortib bormoqda, shu sababli moslashuv choralarini hozirdan rejalashtirish tavsiya etiladi."
        )
    else:
        summary += "Xavflar asosan geologik xarakterga ega — tayyorgarlik va infratuzilma barqarorligi asosiy omil."

    drivers = [f"{HAZARDS[c]['label']}: {HAZARDS[c]['desc'].lower()}" for c, _ in top]
    drivers.append(region.description)
    if region.population > 2_500_000:
        drivers.append(f"Aholi soni yuqori (~{region.population / 1e6:.1f} mln) — taʼsir ostidagi odamlar koʻp.")

    recs = []
    for code, _ in top:
        for title, text, prio in RECOMMENDATIONS.get(code, [])[:2]:
            recs.append({"title": title, "text": text, "priority": prio, "hazard": code})
    recs = recs[:5]

    sources = []
    for code, _ in ranked:
        for s in HAZARDS[code]["sources"]:
            if s not in sources:
                sources.append(s)

    return {
        "overall_score": overall,
        "confidence": max(55, 88 - horizon),
        "summary": summary,
        "scores": scores,
        "timeline": build_timeline(region, hazards, horizon),
        "drivers": drivers[:5],
        "recommendations": recs,
        "satellite_sources": sources[:6],
    }
