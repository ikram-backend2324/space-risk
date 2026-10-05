"""OpenRouter client for SPACE RISK forecasts and the AI analyst chat."""
import json
import logging
import re
from datetime import date

import requests
from django.conf import settings

from . import engine
from .hazards import HAZARDS

log = logging.getLogger("risk")

API_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = """You are SPACE RISK — a geospatial AI analyst built for UzCosmos (Uzbekistan Space Agency).
You forecast future natural and environmental hazard risk for regions of Uzbekistan by reasoning over
satellite-derived indicators (Sentinel-1/2/5P, Landsat-8/9, MODIS, GRACE-FO, GPM, SMAP), historical
disaster records and climate-change trends for Central Asia.
Be realistic and specific to the region's geography (mountains, Fergana Valley, Kyzylkum desert,
Aral Sea basin, Amu Darya / Syr Darya, etc.).
ALWAYS write every human-readable text in Uzbek (Latin script)."""


def _headers():
    return {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": settings.SITE_URL,
        "X-Title": "SPACE RISK",
    }


def _chat(messages, *, json_mode=False, max_tokens=1800, temperature=0.4):
    payload = {
        "model": settings.OPENROUTER_MODEL,
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


def forecast(region, hazards, horizon, notes=""):
    """
    Returns (result_dict, source, model_name). Falls back to the internal engine
    if no key is configured or anything goes wrong, so the demo never breaks.
    """
    base = engine.forecast(region, hazards, horizon, notes)
    if not settings.OPENROUTER_API_KEY:
        return base, "engine", "SPACE RISK Engine v1"

    points = [label for label, _ in engine.timeline_points(horizon)]
    hazard_lines = "\n".join(
        f"- {code} ({HAZARDS[code]['label']}): baseline {region.baseline.get(code, 30)}/100, "
        f"engine projection {base['scores'][code]}/100"
        for code in base["scores"]
    )
    user_prompt = f"""Forecast hazard risk for this region.

REGION: {region.name} (centre: {region.center}; lat {region.lat}, lng {region.lng})
Area: {region.area_km2} km², population: {region.population}
Context: {region.description}
Today: {date.today().isoformat()}. Forecast horizon: {horizon} year(s) → target year {date.today().year + horizon}.
User notes: {notes or "—"}

Hazards to assess (0–100 index; baseline is today's satellite-derived value, engine projection is a
simple trend model you may disagree with):
{hazard_lines}

Return ONLY a JSON object with exactly these keys:
{{
  "overall_score": number 0-100 (composite risk at target year),
  "confidence": integer 0-100,
  "summary": "3-4 sentence executive summary in Uzbek",
  "scores": {{ {", ".join(f'"{c}": number' for c in base["scores"])} }},
  "timeline": [ {len(points)} numbers = overall score at points {points} ],
  "drivers": ["4-5 key risk drivers in Uzbek, concrete to this region"],
  "recommendations": [{{"title": "short Uzbek title", "text": "1-2 sentence actionable Uzbek recommendation", "priority": "high|medium|low"}}] (4-5 items),
  "satellite_sources": ["satellite datasets most relevant for monitoring"]
}}"""

    try:
        text, model = _chat(
            [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_prompt}],
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
    recs = []
    for r in data.get("recommendations") or []:
        if isinstance(r, dict) and r.get("title"):
            prio = r.get("priority") if r.get("priority") in ("high", "medium", "low") else "medium"
            recs.append({"title": str(r["title"])[:140], "text": str(r.get("text", ""))[:600], "priority": prio})

    result = {
        "overall_score": round(_num(data.get("overall_score"), engine.composite(scores)), 1),
        "confidence": int(_num(data.get("confidence"), base["confidence"])),
        "summary": str(data.get("summary") or base["summary"]).strip(),
        "scores": scores,
        "timeline": engine.build_timeline(region, list(scores), horizon, final_scores=scores, overall_path=path),
        "drivers": [str(d) for d in (data.get("drivers") or base["drivers"])][:6],
        "recommendations": recs or base["recommendations"],
        "satellite_sources": [str(s) for s in (data.get("satellite_sources") or base["satellite_sources"])][:8],
    }
    if result["timeline"]:
        # Keep the chart's last point consistent with the headline number.
        result["timeline"][-1]["overall"] = result["overall_score"]
    return result, "ai", model


def ask(prediction, question, history):
    """Answer a follow-up question about a prediction."""
    if not settings.OPENROUTER_API_KEY:
        top = prediction.hazard_rows()[:2]
        names = " va ".join(h["label"].lower() for h in top)
        return (
            "🛰️ AI tahlilchi hozir oflayn rejimda (OPENROUTER_API_KEY sozlanmagan). "
            f"Ichki model boʻyicha {prediction.region.name} uchun asosiy eʼtibor {names} xavflariga qaratilishi kerak. "
            "Toʻliq javob olish uchun administrator OpenRouter kalitini qoʻshishi lozim."
        )

    context = {
        "region": prediction.region.name,
        "horizon_years": prediction.horizon_years,
        "target_year": prediction.target_year,
        "overall_score": prediction.overall_score,
        "level": prediction.get_level_display(),
        "scores": {HAZARDS[c]["label"]: v for c, v in prediction.scores.items() if c in HAZARDS},
        "summary": prediction.summary,
        "recommendations": [r.get("title") for r in prediction.recommendations],
    }
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + "\nAnswer concisely (max ~150 words), use short paragraphs or bullet points. "
                                                      "Forecast context (JSON): " + json.dumps(context, ensure_ascii=False)},
    ]
    for m in history[-8:]:
        messages.append({"role": m.role, "content": m.content})
    messages.append({"role": "user", "content": question})
    try:
        text, _ = _chat(messages, max_tokens=700, temperature=0.5)
        return text.strip() or "Javob olinmadi, qayta urinib koʻring."
    except Exception as exc:
        log.warning("OpenRouter chat failed: %s", exc)
        return "⚠️ AI xizmatiga ulanishda xatolik yuz berdi. Birozdan soʻng qayta urinib koʻring."
