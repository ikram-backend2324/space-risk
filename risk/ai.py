"""OpenRouter client for SPACE RISK forecasts, the AI analyst chat and translations."""
import json
import logging
import re
from datetime import date

import requests
from django.conf import settings

from . import engine, i18n
from .hazards import HAZARDS, hazard, level_for, level_label

log = logging.getLogger("risk")

API_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = """You are SPACE RISK — a geospatial AI analyst built for UzCosmos (Uzbekistan Space Agency).
You forecast future natural and environmental hazard risk for regions of Uzbekistan by reasoning over
satellite-derived indicators (Sentinel-1/2/5P, Landsat-8/9, MODIS, GRACE-FO, GPM, SMAP), historical
disaster records and climate-change trends for Central Asia.
Be realistic and specific to the region's geography (mountains, Fergana Valley, Kyzylkum desert,
Aral Sea basin, Amu Darya / Syr Darya, etc.)."""


KAA_GUIDE = """
KARAKALPAK STYLE GUIDE (follow strictly):
- Alphabet: a á b d e f g ǵ h x ı i j k q l m n ń o ó p r s t u ú v w y z sh c ch. Capital of ı is Í.
- NEVER use Uzbek spellings: no oʻ / gʻ / apostrophes, no "va", "uchun", "xavf", "hudud", "prognoz", "boʻyicha", "kerak boʻladi".
- Use: hám (and), ushın (for), qáwip (risk), aymaq (region), wálayat (province), boljaw (forecast),
  boyınsha (by), usınıs (recommendation), ilaj (measure), jer silkiniw (earthquake), sel hám tasqın (floods),
  qurǵaqshılıq (drought), ıssılıq tolqını (heatwave), suw tanqıslıǵı (water scarcity), shań-duz boranları
  (dust-salt storms), hawanıń pataslanıwı (air pollution), shólge aylanıw (desertification),
  jasalma joldas (satellite), jasalma intellekt (AI), scenariy (scenario), kerek (needed).
- Example sentence: "Aral teńizi aymaǵında shań-duz boranları qáwipi joqarı, sonlıqtan seksewil egiw usınıladı."
"""
KAA_RETRY = ("Rewrite your previous answer in correct Karakalpak (Latin alphabet with á, ǵ, ı, ń, ó, ú, w). "
             "Remove every Uzbek word and every apostrophe letter (oʻ, gʻ). Keep the same meaning and length.")
_UZ_MARKERS = re.compile(r"[ʻʼ‘’']|(?<!\w)(va|uchun|xavf|hudud|prognoz|boʻyicha|kerak boʻladi|qilish|boʻlgan)(?!\w)", re.I)


def looks_uzbek(text):
    """Heuristic: Karakalpak text should not contain Uzbek-only spellings/words."""
    return len(_UZ_MARKERS.findall(text or "")) >= 2


def _language_rule(lang):
    return (f"\nLANGUAGE: write EVERY human-readable text strictly in {i18n.AI_LANGUAGE[lang]}. "
            "Do not mix languages. Keep satellite/mission names (Sentinel, Landsat, MODIS…) as they are.")


def _headers():
    return {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": settings.SITE_URL,
        "X-Title": "SPACE RISK",
    }


def _chat(messages, *, json_mode=False, max_tokens=1800, temperature=0.4, model=None):
    payload = {
        "model": model or settings.OPENROUTER_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    resp = requests.post(API_URL, headers=_headers(), json=payload, timeout=settings.OPENROUTER_TIMEOUT)
    if resp.status_code >= 400 and json_mode:
        # Some models reject response_format — retry without it.
        payload.pop("response_format", None)
        resp = requests.post(API_URL, headers=_headers(), json=payload, timeout=settings.OPENROUTER_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"] or "", data.get("model", settings.OPENROUTER_MODEL)


def _extract_json(text):
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.S)
    if fence:
        text = fence.group(1)
    else:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1:
            text = text[start:end + 1]
    return json.loads(text)


def _num(v, default):
    try:
        return max(0.0, min(100.0, float(v)))
    except (TypeError, ValueError):
        return default


def _clean_recs(items):
    recs = []
    for r in items or []:
        if isinstance(r, dict) and r.get("title"):
            prio = r.get("priority") if r.get("priority") in ("high", "medium", "low") else "medium"
            recs.append({"title": str(r["title"])[:140], "text": str(r.get("text", ""))[:600], "priority": prio})
    return recs


def forecast(region, hazards, horizon, notes="", lang=None):
    """
    Returns (result_dict, source, model_name). Falls back to the internal engine
    if no key is configured or anything goes wrong, so the demo never breaks.
    """
    lang = lang or i18n.get_lang()
    base = engine.forecast(region, hazards, horizon, notes, lang=lang)
    if not settings.OPENROUTER_API_KEY:
        return base, "engine", "SPACE RISK Engine v1"

    points = [label for label, _ in engine.timeline_points(horizon, lang="en")]
    hazard_lines = "\n".join(
        f"- {code} ({hazard(code, 'en')['label']}): baseline {region.baseline.get(code, 30)}/100, "
        f"engine projection {base['scores'][code]}/100"
        for code in base["scores"]
    )
    user_prompt = f"""Forecast hazard risk for this region.

REGION: {engine._region_name(region, 'en')} ({region.name}) (centre: {region.center}; lat {region.lat}, lng {region.lng})
Area: {region.area_km2} km², population: {region.population}
Context: {engine._region_desc(region, 'en')}
Today: {date.today().isoformat()}. Forecast horizon: {horizon} year(s) → target year {date.today().year + horizon}.
User notes: {notes or "—"}

Hazards to assess (0–100 index; baseline is today's satellite-derived value, engine projection is a
simple trend model you may disagree with):
{hazard_lines}

Return ONLY a JSON object with exactly these keys (JSON keys stay in English):
{{
  "overall_score": number 0-100 (composite risk at target year),
  "confidence": integer 0-100,
  "summary": "3-4 sentence executive summary",
  "scores": {{ {", ".join(f'"{c}": number' for c in base["scores"])} }},
  "timeline": [ {len(points)} numbers = overall score at points {points} ],
  "drivers": ["4-5 key risk drivers, concrete to this region"],
  "recommendations": [{{"title": "short title", "text": "1-2 sentence actionable recommendation", "priority": "high|medium|low"}}] (4-5 items),
  "satellite_sources": ["satellite datasets most relevant for monitoring"]
}}"""

    try:
        text, model = _chat(
            [{"role": "system", "content": SYSTEM_PROMPT + _language_rule(lang)}, {"role": "user", "content": user_prompt}],
            json_mode=True,
        )
        data = _extract_json(text)
    except Exception as exc:  # network, HTTP, parsing — fall back gracefully
        log.warning("OpenRouter forecast failed, using engine: %s", exc)
        return base, "engine", "SPACE RISK Engine v1"

    scores = {c: round(_num((data.get("scores") or {}).get(c), base["scores"][c]), 1) for c in base["scores"]}
    path = data.get("timeline") if isinstance(data.get("timeline"), list) else None
    if path:
        path = [_num(v.get("overall") if isinstance(v, dict) else v, 0) for v in path]

    result = {
        "overall_score": round(_num(data.get("overall_score"), engine.composite(scores)), 1),
        "confidence": int(_num(data.get("confidence"), base["confidence"])),
        "summary": str(data.get("summary") or base["summary"]).strip(),
        "scores": scores,
        "timeline": engine.build_timeline(region, list(scores), horizon, final_scores=scores, overall_path=path),
        "drivers": [str(d) for d in (data.get("drivers") or base["drivers"])][:6],
        "recommendations": _clean_recs(data.get("recommendations")) or base["recommendations"],
        "satellite_sources": [str(s) for s in (data.get("satellite_sources") or base["satellite_sources"])][:8],
    }
    if result["timeline"]:
        # Keep the chart's last point consistent with the headline number.
        result["timeline"][-1]["overall"] = result["overall_score"]
    if lang == "kaa":
        # Language models write Karakalpak unreliably (mixing in Uzbek/Kazakh). Keep the AI's numbers,
        # but take the summary, drivers and recommendations from the hand-checked Karakalpak catalog.
        result.update(engine.narrative(region, scores, result["overall_score"], horizon, lang="kaa"))
    return result, "ai", model


def translate(prediction, lang):
    """Translate an AI forecast's text into ``lang``. Returns dict or raises.

    Not used for Karakalpak — callers use the hand-checked catalog text instead.
    """
    if lang == "kaa":
        raise ValueError("Karakalpak uses catalog text, not machine translation")
    payload = {
        "summary": prediction.summary,
        "drivers": prediction.drivers,
        "recommendations": [{"title": r.get("title", ""), "text": r.get("text", ""), "priority": r.get("priority", "medium")}
                            for r in prediction.recommendations],
    }
    messages = [
        {"role": "system", "content": "You are a professional translator for a geospatial risk platform." + _language_rule(lang)
         + "\nTranslate the JSON values faithfully. Keep the JSON structure, keys, numbers and the 'priority' values unchanged. "
           "Return ONLY the JSON object."},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]
    text, _ = _chat(messages, json_mode=True, max_tokens=1800, temperature=0.2)
    data = _extract_json(text)
    out = {
        "summary": str(data.get("summary") or "").strip(),
        "drivers": [str(d) for d in data.get("drivers") or []][:6],
        "recommendations": _clean_recs(data.get("recommendations")),
    }
    if not out["summary"] or not out["recommendations"]:
        raise ValueError("incomplete translation")
    return out


def ask(prediction, question, history, lang=None):
    """Answer a follow-up question about a prediction in ``lang``."""
    lang = lang or i18n.get_lang()
    if not settings.OPENROUTER_API_KEY:
        names = i18n.join_and([i18n.lower_first(h["label"], lang) for h in prediction.hazard_rows()[:2]], lang)
        return i18n.t("ai.offline", lang, region=engine._region_name(prediction.region, lang), hazards=names)

    context = {
        "region": engine._region_name(prediction.region, "en"),
        "horizon_years": prediction.horizon_years,
        "target_year": prediction.target_year,
        "overall_score": prediction.overall_score,
        "level": level_label(level_for(prediction.overall_score), "en"),
        "scores": {hazard(c, "en")["label"]: v for c, v in prediction.scores.items() if c in HAZARDS},
        "summary": prediction.summary,
        "recommendations": [r.get("title") for r in prediction.recommendations],
    }
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + _language_rule(lang)
         + "\nAnswer concisely (max ~150 words), use short paragraphs or bullet points. "
           "Forecast context (JSON): " + json.dumps(context, ensure_ascii=False)},
    ]
    for m in history[-8:]:
        messages.append({"role": m.role, "content": m.content})
    messages.append({"role": "user", "content": question})
    model = (settings.OPENROUTER_MODEL_KAA or None) if lang == "kaa" else None
    if lang == "kaa":
        messages[0]["content"] += KAA_GUIDE
    try:
        text, _ = _chat(messages, max_tokens=700, temperature=0.4, model=model)
        if lang == "kaa" and looks_uzbek(text):
            messages.append({"role": "assistant", "content": text})
            messages.append({"role": "user", "content": KAA_RETRY})
            text, _ = _chat(messages, max_tokens=700, temperature=0.2, model=model)
        return text.strip() or i18n.t("ai.empty", lang)
    except Exception as exc:
        log.warning("OpenRouter chat failed: %s", exc)
        return i18n.t("ai.error", lang)
