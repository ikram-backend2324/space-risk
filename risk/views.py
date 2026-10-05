import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from . import ai
from .hazards import HAZARDS, HORIZONS, LEVEL_COLORS, LEVEL_LABELS, level_for
from .models import ChatMessage, Prediction, Region


def _regions_payload():
    return [r.as_map_dict() for r in Region.objects.all()]


def landing(request):
    regions = list(Region.objects.all())
    ctx = {
        "regions_json": [r.as_map_dict() for r in regions],
        "hazards": HAZARDS,
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
            "labels": [HAZARDS[c]["label"] for c in national],
            "values": list(national.values()),
            "colors": [HAZARDS[c]["color"] for c in national],
        },
        "levels_json": {
            "labels": [LEVEL_LABELS[c] for c in by_level],
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
        hazards = [h for h in request.POST.getlist("hazards") if h in HAZARDS]
        if not hazards:
            messages.error(request, "Kamida bitta xavf turini tanlang.")
            return redirect(f"{request.path}?region={region.slug}")
        notes = request.POST.get("notes", "").strip()[:1000]

        result, source, model_name = ai.forecast(region, hazards, horizon, notes)
        pred = Prediction.objects.create(
            user=request.user, region=region, horizon_years=horizon, hazards=hazards, notes=notes,
            overall_score=result["overall_score"], level=level_for(result["overall_score"]),
            confidence=result["confidence"], summary=result["summary"], scores=result["scores"],
            timeline=result["timeline"], drivers=result["drivers"], recommendations=result["recommendations"],
            satellite_sources=result["satellite_sources"], source=source, model_name=model_name,
        )
        if source == "engine" and settings.OPENROUTER_API_KEY:
            messages.warning(request, "AI xizmati javob bermadi — prognoz ichki model asosida tuzildi.")
        return redirect(pred)

    ctx = {
        "regions": regions,
        "regions_json": _regions_payload(),
        "hazards": HAZARDS,
        "horizons": HORIZONS,
        "selected": request.GET.get("region", ""),
    }
    return render(request, "risk/predict.html", ctx)


@login_required
def detail(request, pk):
    pred = get_object_or_404(Prediction.objects.select_related("region"), pk=pk, user=request.user)
    rows = pred.hazard_rows()
    chart = {
        "radar": {
            "labels": [r["label"] for r in rows],
            "now": [pred.region.baseline.get(r["code"], 0) for r in rows],
            "future": [r["score"] for r in rows],
        },
        "timeline": {
            "labels": [p["label"] for p in pred.timeline],
            "overall": [p["overall"] for p in pred.timeline],
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
        "p": pred, "rows": rows, "chart": chart, "chat": pred.messages.all(),
        "level_label": LEVEL_LABELS.get(pred.level, ""),
    })


@login_required
def history(request):
    preds = request.user.predictions.select_related("region")
    region = request.GET.get("region")
    if region:
        preds = preds.filter(region__slug=region)
    return render(request, "risk/history.html", {
        "predictions": preds, "regions": Region.objects.all(), "current_region": region,
    })


@login_required
@require_POST
def delete(request, pk):
    pred = get_object_or_404(Prediction, pk=pk, user=request.user)
    pred.delete()
    messages.success(request, "Prognoz oʻchirildi.")
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
        return JsonResponse({"error": "Savol boʻsh"}, status=400)
    question = question[:800]
    history = list(pred.messages.all())
    answer = ai.ask(pred, question, history)
    ChatMessage.objects.create(prediction=pred, role="user", content=question)
    ChatMessage.objects.create(prediction=pred, role="assistant", content=answer)
    return JsonResponse({"answer": answer})


def regions_api(request):
    return JsonResponse({"regions": _regions_payload()})
