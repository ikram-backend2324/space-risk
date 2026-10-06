import io
import json
import logging
from urllib.parse import urlparse

from django.conf import settings
from django.core.cache import cache
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.db.models import Avg, Count
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from . import ai, engine, i18n
from .hazards import HAZARDS, HORIZONS, LEVEL_COLORS, hazard, hazards, level_for, level_label, source_label
from .i18n import t
from .models import ChatMessage, Prediction, Region

log = logging.getLogger("risk")


def _throttled(request, action, seconds):
    """True if this user did ``action`` less than ``seconds`` ago (protects the OpenRouter budget)."""
    key = f"rl:{action}:{request.user.pk}"
    if cache.get(key):
        return True
    cache.set(key, 1, seconds)
    return False


def download_android(request):
    """Serve the Android APK as a real file download (Chrome, Yandex, Edge, Firefox, Safari…)."""
    path = settings.ANDROID_APK_PATH
    if not path.exists():
        raise Http404("APK not found")
    response = FileResponse(open(path, "rb"), as_attachment=True,
                            filename=f"SPACE-RISK-{settings.ANDROID_APK_VERSION}.apk",
                            content_type="application/vnd.android.package-archive")
    response["Cache-Control"] = "no-cache"
    response["X-Content-Type-Options"] = "nosniff"
    return response


QR_TARGETS = {"telegram": lambda r: settings.TELEGRAM_BOT_URL, "android": lambda r: r.build_absolute_uri("/download/android/")}


def qr_code(request, target):
    """QR code (SVG) for the Telegram bot or the APK download link — dark modules on white, so every camera can read it."""
    import segno

    make = QR_TARGETS.get(target)
    if make is None:
        raise Http404
    buf = io.BytesIO()
    segno.make(make(request), error="m").save(buf, kind="svg", scale=8, border=2, dark="#0b1230", light="#ffffff", xmldecl=False, svgns=True)
    response = HttpResponse(buf.getvalue(), content_type="image/svg+xml")
    response["Cache-Control"] = "public, max-age=86400"
    return response


def _regions_payload():
    return [r.as_map_dict() for r in Region.objects.all()]


def set_language(request, code):
    lang = i18n.normalize(code) or i18n.DEFAULT
    nxt = request.GET.get("next") or request.META.get("HTTP_REFERER") or "/"
    if not url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        nxt = "/"
    # Drop a stale ?lang= from the target so the cookie wins.
    parsed = urlparse(nxt)
    if "lang=" in (parsed.query or ""):
        nxt = parsed.path or "/"
    response = redirect(nxt)
    response.set_cookie(i18n.COOKIE, lang, max_age=365 * 24 * 3600, samesite="Lax")
    return response


def localized_text(pred, lang, allow_ai=True):
    """Summary/drivers/recommendations of a forecast in ``lang``.

    Same language → original text. Built-in engine forecasts → regenerated in ``lang``.
    AI forecasts → cached AI translation, translated now (if allowed), or an engine-written
    summary of the same scores as a fallback.
    """
    original = {"summary": pred.summary, "drivers": pred.drivers, "recommendations": pred.recommendations, "translated": False}
    if lang == pred.language:
        return original
    fallback = {**engine.narrative(pred.region, pred.scores, pred.overall_score, pred.horizon_years,
                                   pred.created_at.year, lang), "translated": False}
    if pred.source == "engine" or lang == "kaa":
        # Karakalpak always uses the hand-checked catalog (no machine translation).
        return fallback
    cached = (pred.translations or {}).get(lang)
    if cached:
        return {**cached, "translated": True}
    if allow_ai and settings.OPENROUTER_API_KEY:
        try:
            data = ai.translate(pred, lang)
            pred.translations = {**(pred.translations or {}), lang: data}
            pred.save(update_fields=["translations"])
            return {**data, "translated": True}
        except Exception as exc:
            log.warning("Translation of prediction %s to %s failed: %s", pred.pk, lang, exc)
    return fallback


def landing(request):
    regions = list(Region.objects.all())
    ctx = {
        "regions_json": [r.as_map_dict() for r in regions],
        "hazards": hazards(),
        "stats": {
            "regions": len(regions),
            "hazards": len(HAZARDS),
            "predictions": Prediction.objects.count(),
            "population": round(sum(r.population for r in regions) / 1e6, 1),
        },
        "top_regions": sorted(regions, key=lambda r: r.composite, reverse=True)[:4],
    }
    return render(request, "risk/landing.html", ctx)


@login_required
def dashboard(request):
    regions = list(Region.objects.all())
    mine = request.user.predictions.select_related("region")
    agg = mine.aggregate(avg=Avg("overall_score"), n=Count("id"))
    by_level = {code: 0 for code in LEVEL_COLORS}
    for row in mine.values("level").annotate(c=Count("id")):
        by_level[row["level"]] = row["c"]

    national = {code: round(sum(r.baseline.get(code, 0) for r in regions) / max(len(regions), 1), 1) for code in HAZARDS}
    ctx = {
        "regions": sorted(regions, key=lambda r: r.composite, reverse=True),
        "regions_json": [r.as_map_dict() for r in regions],
        "recent": mine[:6],
        "total": agg["n"] or 0,
        "avg_score": round(agg["avg"] or 0),
        "critical": by_level["critical"] + by_level["high"],
        "national_json": {
            "labels": [hazard(c)["label"] for c in national],
            "values": list(national.values()),
            "colors": [HAZARDS[c]["color"] for c in national],
        },
        "levels_json": {
            "labels": [level_label(c) for c in by_level],
            "values": list(by_level.values()),
            "colors": [LEVEL_COLORS[c] for c in by_level],
        },
    }
    return render(request, "risk/dashboard.html", ctx)


@login_required
def predict(request):
    regions = Region.objects.all()
    if request.method == "POST":
        region = get_object_or_404(Region, slug=request.POST.get("region"))
        try:
            horizon = int(request.POST.get("horizon", 5))
        except ValueError:
            horizon = 5
        if horizon not in dict(HORIZONS):
            horizon = 5
        selected = [h for h in request.POST.getlist("hazards") if h in HAZARDS]
        if not selected:
            messages.error(request, t("msg.pick_hazard"))
            return redirect(f"{request.path}?region={region.slug}")
        notes = request.POST.get("notes", "").strip()[:1000]
        if _throttled(request, "predict", 15):
            messages.warning(request, t("msg.slow_down"))
            return redirect(f"{request.path}?region={region.slug}")

        lang = request.LANG
        result, source, model_name = ai.forecast(region, selected, horizon, notes, lang=lang)
        pred = Prediction.objects.create(
            user=request.user, region=region, horizon_years=horizon, hazards=selected, notes=notes,
            overall_score=result["overall_score"], level=level_for(result["overall_score"]),
            confidence=result["confidence"], summary=result["summary"], scores=result["scores"],
            timeline=result["timeline"], drivers=result["drivers"], recommendations=result["recommendations"],
            satellite_sources=result["satellite_sources"], source=source, model_name=model_name, language=lang,
        )
        if source == "engine" and settings.OPENROUTER_API_KEY:
            messages.warning(request, t("msg.ai_fallback"))
        return redirect(pred)

    ctx = {
        "regions": regions,
        "regions_json": _regions_payload(),
        "hazards": hazards(),
        "horizons": [(n, i18n.years(n)) for n, _ in HORIZONS],
        "selected": request.GET.get("region", ""),
    }
    return render(request, "risk/predict.html", ctx)


def detail(request, pk):
    pred = get_object_or_404(Prediction.objects.select_related("region"), pk=pk)
    owner = request.user.is_authenticated and pred.user_id == request.user.id
    if not owner:
        # Links shared from the app / bot carry a signed token: read-only view for anyone.
        if not pred.share_valid(request.GET.get("share")):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            raise Http404
    lang = request.LANG
    rows = pred.hazard_rows()
    text = localized_text(pred, lang, allow_ai=owner)
    labels = [label for label, _ in engine.timeline_points(pred.horizon_years, lang, start=pred.created_at.year)]
    if len(labels) != len(pred.timeline):
        labels = [p.get("label", "") for p in pred.timeline]
    chart = {
        "radar": {
            "labels": [r["label"] for r in rows],
            "now": [pred.region.baseline.get(r["code"], 0) for r in rows],
            "future": [r["score"] for r in rows],
            "colors": [r["color"] for r in rows],
            "today": t("detail.chart_today"),
            "forecast": t("detail.chart_forecast"),
        },
        "timeline": {
            "labels": labels,
            "overall": [p["overall"] for p in pred.timeline],
            "overall_label": t("detail.chart_overall"),
            "series": [
                {"label": r["label"], "color": r["color"], "data": [p["hazards"].get(r["code"]) for p in pred.timeline]}
                for r in rows[:4]
            ],
        },
        "bars3d": [{"label": r["label"], "score": r["score"], "color": r["color"]} for r in rows],
        "score": pred.overall_score,
        "color": pred.color,
    }
    return render(request, "risk/detail.html", {
        "p": pred, "rows": rows, "chart": chart, "chat": pred.messages.filter(language=lang), "text": text,
        "sources": [source_label(s, lang) for s in pred.satellite_sources],
        "horizon_text": i18n.years(pred.horizon_years), "owner": owner,
    })


@login_required
def history(request):
    preds = list(request.user.predictions.select_related("region"))
    region = request.GET.get("region")
    if region:
        preds = [p for p in preds if p.region.slug == region]
    for p in preds:  # no AI calls on the list page — cached or engine-written text only
        p.display_summary = localized_text(p, request.LANG, allow_ai=False)["summary"]
    return render(request, "risk/history.html", {
        "predictions": preds, "regions": Region.objects.all(), "current_region": region,
    })


@login_required
@require_POST
def delete(request, pk):
    pred = get_object_or_404(Prediction, pk=pk, user=request.user)
    pred.delete()
    messages.success(request, t("msg.deleted"))
    return redirect("risk:history")


@login_required
@require_POST
def ask(request, pk):
    pred = get_object_or_404(Prediction, pk=pk, user=request.user)
    try:
        question = json.loads(request.body or "{}").get("question", "").strip()
    except json.JSONDecodeError:
        question = ""
    if not question:
        return JsonResponse({"error": t("ai.empty_question")}, status=400)
    question = question[:800]
    if _throttled(request, "ask", 4):
        return JsonResponse({"error": t("msg.slow_down")}, status=429)
    lang = request.LANG
    history_msgs = list(pred.messages.filter(language=lang))
    answer = ai.ask(pred, question, history_msgs, lang=lang)
    ChatMessage.objects.create(prediction=pred, role="user", content=question, language=lang)
    ChatMessage.objects.create(prediction=pred, role="assistant", content=answer, language=lang)
    return JsonResponse({"answer": answer})


def regions_api(request):
    """Public region data. Supports ?lang=uz|en|ru|kaa (handled by LanguageMiddleware)."""
    return JsonResponse({"lang": request.LANG, "regions": _regions_payload()})
