"""JSON API (v1) for the SPACE RISK Android app and Telegram bot.

Auth: ``Authorization: Token <key>`` (from /auth/login or /auth/register).
Language: ``X-Lang: uz|en|ru|kaa`` header or ``?lang=`` (handled by LanguageMiddleware).
"""
import json
from functools import wraps

from django.conf import settings
from django.contrib.auth import authenticate
from django.core.cache import cache
from django.db.models import Avg, Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from accounts.forms import ProfileForm, RegisterForm
from accounts.models import Profile
from risk import ai, engine, i18n
from risk.hazards import (HAZARDS, HORIZONS, LEVEL_COLORS, LEVELS, hazard, level_for, level_label, priority_label,
                          source_label)
from risk.i18n import t
from risk.models import ChatMessage, Prediction, Region
from risk.views import localized_text

from .models import ApiToken

API_VERSION = "1.0"


# ------------------------------------------------------------------ helpers
def ok(data, status=200):
    return JsonResponse(data, status=status, safe=not isinstance(data, list), json_dumps_params={"ensure_ascii": False})


def fail(message, status=400, errors=None):
    body = {"error": str(message)}
    if errors:
        body["errors"] = errors
    return ok(body, status)


def body(request):
    try:
        return json.loads(request.body or "{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


def throttled(key, seconds):
    if cache.get(key):
        return True
    cache.set(key, 1, seconds)
    return False


def client_ip(request):
    return (request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip() or request.META.get("REMOTE_ADDR", ""))


def token_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        header = request.headers.get("Authorization", "")
        key = header.split(" ", 1)[1].strip() if " " in header else ""
        token = ApiToken.objects.select_related("user").filter(key=key).first() if key else None
        if token is None or not token.user.is_active:
            return fail(t("api.auth_required"), 401)
        if not token.last_used_at or (timezone.now() - token.last_used_at).total_seconds() > 300:
            ApiToken.objects.filter(pk=token.pk).update(last_used_at=timezone.now())
        request.user = token.user
        request.api_token = token
        return view(request, *args, **kwargs)
    return wrapper


def form_errors(form):
    return {field: [str(e) for e in errs] for field, errs in form.errors.items()}


def user_payload(user):
    profile, _ = Profile.objects.get_or_create(user=user)
    preds = user.predictions
    return {
        "id": user.pk, "username": user.username, "first_name": user.first_name, "last_name": user.last_name,
        "email": user.email, "organization": profile.organization, "position": profile.position,
        "initials": profile.initials, "date_joined": user.date_joined.isoformat(), "is_staff": user.is_staff,
        "stats": {"forecasts": preds.count(), "high_risk": preds.filter(level__in=["high", "critical"]).count()},
    }


def region_payload(region, full=False):
    data = {
        "slug": region.slug, "name": region.display_name, "lat": region.lat, "lng": region.lng,
        "score": region.composite, "level": region.level, "level_label": region.level_label, "color": region.color,
        "population": region.population, "top": [h["label"] for h in region.top_hazards(2)],
    }
    if full:
        data.update(description=region.display_description, center=region.center, area_km2=region.area_km2,
                    baseline=region.baseline)
    return data


def forecast_summary(pred, lang):
    return {
        "id": pred.pk, "region": {"slug": pred.region.slug, "name": pred.region.display_name},
        "horizon": pred.horizon_years, "horizon_label": i18n.years(pred.horizon_years, lang), "target_year": pred.target_year,
        "overall_score": pred.overall_score, "level": pred.level, "level_label": pred.level_label, "color": pred.color,
        "source": pred.source, "created_at": pred.created_at.isoformat(), "ago": i18n.ago(pred.created_at, lang),
        "summary": localized_text(pred, lang, allow_ai=False)["summary"],
    }


def forecast_detail(pred, lang):
    rows = pred.hazard_rows()
    text = localized_text(pred, lang)
    labels = [label for label, _ in engine.timeline_points(pred.horizon_years, lang, start=pred.created_at.year)]
    if len(labels) != len(pred.timeline):
        labels = [p.get("label", "") for p in pred.timeline]
    data = forecast_summary(pred, lang)
    data.update({
        "summary": text["summary"], "translated": text["translated"], "confidence": pred.confidence,
        "model_name": pred.model_name, "language": pred.language, "notes": pred.notes,
        "region": region_payload(pred.region, full=True),
        "hazards": [{"code": r["code"], "label": r["label"], "desc": r["desc"], "icon": r["icon"], "color": r["color"],
                     "score": r["score"], "baseline": pred.region.baseline.get(r["code"], 0), "level": r["level"],
                     "level_label": r["level_label"], "level_color": r["level_color"]} for r in rows],
        "timeline": {
            "labels": labels, "overall": [p["overall"] for p in pred.timeline],
            "series": [{"code": r["code"], "label": r["label"], "color": r["color"],
                        "data": [p["hazards"].get(r["code"]) for p in pred.timeline]} for r in rows],
        },
        "drivers": text["drivers"],
        "recommendations": [{**r, "priority": r.get("priority", "medium"), "priority_label": priority_label(r.get("priority", "medium"), lang)}
                            for r in text["recommendations"]],
        "sources": [source_label(s, lang) for s in pred.satellite_sources],
        "chat": [{"role": m.role, "content": m.content, "created_at": m.created_at.isoformat()}
                 for m in pred.messages.filter(language=lang)],
        "web_url": settings.SITE_URL.rstrip("/") + pred.get_absolute_url(),
    })
    return data


# ------------------------------------------------------------------ public
@require_http_methods(["GET"])
def meta(request):
    lang = request.LANG
    return ok({
        "version": API_VERSION, "lang": lang, "ai_online": bool(settings.OPENROUTER_API_KEY),
        "languages": [{"code": c, "name": n, "short": s} for c, n, s in i18n.LANGUAGES],
        "hazards": [{"code": c, **{k: v for k, v in hazard(c, lang).items() if k in ("label", "desc", "color", "icon", "sources", "trend")}}
                    for c in HAZARDS],
        "levels": [{"code": c, "label": level_label(c, lang), "color": col, "from": th} for c, _, col, th in LEVELS],
        "horizons": [{"value": n, "label": i18n.years(n, lang)} for n, _ in HORIZONS],
        "regions": [region_payload(r, full=True) for r in Region.objects.all()],
        "tagline": t("site.tagline"),
    })


@csrf_exempt
@require_http_methods(["POST"])
def register(request):
    if throttled(f"api:reg:{client_ip(request)}", 3):
        return fail(t("msg.slow_down"), 429)
    data = body(request)
    form = RegisterForm(data={k: data.get(k, "") for k in ("first_name", "username", "email", "password")})
    if not form.is_valid():
        return fail(t("err.generic"), 400, form_errors(form))
    user = form.save()
    token = ApiToken.objects.create(user=user, device=str(data.get("device", ""))[:120])
    return ok({"token": token.key, "user": user_payload(user)}, 201)


@csrf_exempt
@require_http_methods(["POST"])
def login(request):
    ip = client_ip(request)
    attempts = cache.get(f"api:login:{ip}", 0)
    if attempts >= 10:
        return fail(t("msg.slow_down"), 429)
    data = body(request)
    user = authenticate(request, username=str(data.get("login", "")).strip(), password=str(data.get("password", "")))
    if user is None:
        cache.set(f"api:login:{ip}", attempts + 1, 300)
        return fail(t("err.invalid_login"), 400)
    token = ApiToken.objects.create(user=user, device=str(data.get("device", ""))[:120])
    return ok({"token": token.key, "user": user_payload(user)})


# ------------------------------------------------------------------ authenticated
@csrf_exempt
@require_http_methods(["POST"])
@token_required
def logout(request):
    request.api_token.delete()
    return ok({"ok": True})


@csrf_exempt
@require_http_methods(["GET", "PATCH", "POST"])
@token_required
def me(request):
    if request.method == "GET":
        return ok(user_payload(request.user))
    profile, _ = Profile.objects.get_or_create(user=request.user)
    data = body(request)
    current = {"first_name": request.user.first_name, "last_name": request.user.last_name, "email": request.user.email,
               "organization": profile.organization, "position": profile.position}
    current.update({k: v for k, v in data.items() if k in current})
    form = ProfileForm(data=current, instance=profile, user=request.user)
    if not form.is_valid():
        return fail(t("err.generic"), 400, form_errors(form))
    form.save()
    return ok(user_payload(request.user))


@require_http_methods(["GET"])
@token_required
def dashboard(request):
    lang = request.LANG
    regions = list(Region.objects.all())
    mine = request.user.predictions.select_related("region")
    agg = mine.aggregate(avg=Avg("overall_score"), n=Count("id"))
    by_level = {code: 0 for code in LEVEL_COLORS}
    for row in mine.values("level").annotate(c=Count("id")):
        by_level[row["level"]] = row["c"]
    national = {c: round(sum(r.baseline.get(c, 0) for r in regions) / max(len(regions), 1), 1) for c in HAZARDS}
    return ok({
        "total": agg["n"] or 0, "avg_score": round(agg["avg"] or 0), "high_critical": by_level["high"] + by_level["critical"],
        "regions_count": len(regions),
        "national": [{"code": c, "label": hazard(c, lang)["label"], "color": HAZARDS[c]["color"], "value": v} for c, v in national.items()],
        "levels": [{"code": c, "label": level_label(c, lang), "color": LEVEL_COLORS[c], "count": n} for c, n in by_level.items()],
        "ranking": [region_payload(r) for r in sorted(regions, key=lambda r: r.composite, reverse=True)],
        "recent": [forecast_summary(p, lang) for p in mine[:6]],
    })


@csrf_exempt
@require_http_methods(["GET", "POST"])
@token_required
def forecasts(request):
    lang = request.LANG
    if request.method == "GET":
        qs = request.user.predictions.select_related("region")
        if request.GET.get("region"):
            qs = qs.filter(region__slug=request.GET["region"])
        return ok({"results": [forecast_summary(p, lang) for p in qs[:100]]})

    data = body(request)
    region = Region.objects.filter(slug=data.get("region")).first()
    if region is None:
        return fail(t("js.pick_region"), 400)
    try:
        horizon = int(data.get("horizon", 5))
    except (TypeError, ValueError):
        horizon = 5
    if horizon not in dict(HORIZONS):
        horizon = 5
    selected = [h for h in data.get("hazards") or [] if h in HAZARDS]
    if not selected:
        return fail(t("msg.pick_hazard"), 400)
    if throttled(f"rl:predict:{request.user.pk}", 15):
        return fail(t("msg.slow_down"), 429)
    notes = str(data.get("notes", "")).strip()[:1000]
    result, source, model_name = ai.forecast(region, selected, horizon, notes, lang=lang)
    pred = Prediction.objects.create(
        user=request.user, region=region, horizon_years=horizon, hazards=selected, notes=notes,
        overall_score=result["overall_score"], level=level_for(result["overall_score"]), confidence=result["confidence"],
        summary=result["summary"], scores=result["scores"], timeline=result["timeline"], drivers=result["drivers"],
        recommendations=result["recommendations"], satellite_sources=result["satellite_sources"],
        source=source, model_name=model_name, language=lang,
    )
    return ok(forecast_detail(pred, lang), 201)


@csrf_exempt
@require_http_methods(["GET", "DELETE"])
@token_required
def forecast(request, pk):
    pred = get_object_or_404(Prediction.objects.select_related("region"), pk=pk, user=request.user)
    if request.method == "DELETE":
        pred.delete()
        return ok({"ok": True, "message": t("msg.deleted")})
    return ok(forecast_detail(pred, request.LANG))


@csrf_exempt
@require_http_methods(["POST"])
@token_required
def ask(request, pk):
    pred = get_object_or_404(Prediction, pk=pk, user=request.user)
    question = str(body(request).get("question", "")).strip()[:800]
    if not question:
        return fail(t("ai.empty_question"), 400)
    if throttled(f"rl:ask:{request.user.pk}", 4):
        return fail(t("msg.slow_down"), 429)
    lang = request.LANG
    history = list(pred.messages.filter(language=lang))
    answer = ai.ask(pred, question, history, lang=lang)
    ChatMessage.objects.create(prediction=pred, role="user", content=question, language=lang)
    ChatMessage.objects.create(prediction=pred, role="assistant", content=answer, language=lang)
    return ok({"answer": answer})


@require_http_methods(["GET"])
def public_scenario(request):
    """Deterministic scenario (no AI, no account) — used by the Telegram bot for curated, localized text."""
    lang = request.LANG
    region = Region.objects.filter(slug=request.GET.get("region")).first()
    if region is None:
        return fail(t("js.pick_region"), 400)
    try:
        horizon = int(request.GET.get("horizon", 5))
    except ValueError:
        horizon = 5
    if horizon not in dict(HORIZONS):
        horizon = 5
    selected = [h for h in request.GET.get("hazards", "").split(",") if h in HAZARDS] or list(HAZARDS)
    result = engine.forecast(region, selected, horizon, lang=lang)
    return ok({
        "region": region_payload(region), "horizon": horizon, "horizon_label": i18n.years(horizon, lang),
        "overall_score": result["overall_score"], "level": level_for(result["overall_score"]),
        "level_label": level_label(level_for(result["overall_score"]), lang), "confidence": result["confidence"],
        "scores": result["scores"], "summary": result["summary"], "drivers": result["drivers"],
        "recommendations": [{**r, "priority_label": priority_label(r["priority"], lang)} for r in result["recommendations"]],
        "sources": [source_label(s, lang) for s in result["satellite_sources"]],
    })
