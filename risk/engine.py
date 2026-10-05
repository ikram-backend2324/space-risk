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

from . import i18n
from .hazards import HAZARDS, hazard, level_for, level_label
from .locale_content import MONTHS_SHORT, NARRATIVE, RECOMMENDATIONS

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


def timeline_points(horizon, lang=None, start=None):
    """(label, years-from-start) pairs for the chart."""
    start = start or date.today().year
    if horizon == 1:
        mo = MONTHS_SHORT[lang or i18n.get_lang()]
        return [(f"{start}", 0), (f"+3 {mo}", 0.25), (f"+6 {mo}", 0.5), (f"+9 {mo}", 0.75), (f"{start + 1}", 1)]
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


def _decimal(value, lang):
    text = f"{value:.1f}"
    return text if lang == "en" else text.replace(".", ",")


def narrative(region, scores, overall, horizon, start_year=None, lang=None):
    """Summary, drivers, recommendations and sources in ``lang``, built from structured scores."""
    lang = lang or i18n.get_lang()
    scores = {c: v for c, v in scores.items() if c in HAZARDS}
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    top = ranked[:3]
    year = (start_year or date.today().year) + horizon
    region_name = _region_name(region, lang)

    top_txt = ", ".join(f"{i18n.lower_first(hazard(c, lang)['label'], lang)} ({v:.0f})" for c, v in top)
    summary = NARRATIVE["summary"][lang].format(
        region=region_name, year=year, score=f"{overall:.0f}", level=level_label(level_for(overall), lang), top=top_txt)
    rising = [c for c, _ in ranked if HAZARDS[c]["trend"] >= 0.8][:2]
    if rising:
        names = i18n.join_and([i18n.lower_first(hazard(c, lang)["label"], lang) for c in rising], lang)
        summary += " " + NARRATIVE["rising"][lang].format(list=names)
    else:
        summary += " " + NARRATIVE["geological"][lang]

    drivers = []
    for c, _ in top:
        h = hazard(c, lang)
        drivers.append(f"{h['label']}: {i18n.lower_first(h['desc'], lang)}")
    drivers.append(_region_desc(region, lang))
    if region.population > 2_500_000:
        drivers.append(NARRATIVE["population"][lang].format(n=_decimal(region.population / 1e6, lang)))

    recs = []
    for code, _ in top:
        for title, text, prio in RECOMMENDATIONS.get(code, [])[:2]:
            recs.append({"title": title[lang], "text": text[lang], "priority": prio, "hazard": code})

    sources = []
    for code, _ in ranked:
        for src in HAZARDS[code]["sources"]:
            if src not in sources:
                sources.append(src)

    return {"summary": summary, "drivers": drivers[:5], "recommendations": recs[:5], "satellite_sources": sources[:6]}


def _region_name(region, lang):
    from .hazards import region_text
    return region_text(region.slug, region.name, region.description, lang)[0]


def _region_desc(region, lang):
    from .hazards import region_text
    return region_text(region.slug, region.name, region.description, lang)[1]


def forecast(region, hazards, horizon, notes="", lang=None):
    lang = lang or i18n.get_lang()
    hazards = [h for h in hazards if h in HAZARDS] or list(HAZARDS)
    scores = {code: project(region.baseline.get(code, 30), code, horizon, region.slug) for code in hazards}
    overall = composite(scores)
    return {
        "overall_score": overall,
        "confidence": max(55, 88 - horizon),
        "scores": scores,
        "timeline": build_timeline(region, hazards, horizon),
        **narrative(region, scores, overall, horizon, lang=lang),
    }
