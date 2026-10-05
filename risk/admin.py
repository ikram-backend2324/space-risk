from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import ChatMessage, Prediction, Region


def badge(text, color):
    return format_html(
        '<span style="background:{0}22;color:{0};border:1px solid {0}66;padding:2px 10px;'
        'border-radius:999px;font-weight:600;font-size:12px">{1}</span>', color, text)


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ("name", "center", "population_fmt", "area_km2", "risk_badge", "top_hazard", "prediction_count")
    search_fields = ("name", "center")
    prepopulated_fields = {"slug": ("name",)}
    list_per_page = 20

    @admin.display(description="Aholisi")
    def population_fmt(self, obj):
        return f"{obj.population / 1e6:.2f} mln"

    @admin.display(description="Bazaviy xavf")
    def risk_badge(self, obj):
        return badge(f"{obj.composite}/100", obj.color)

    @admin.display(description="Asosiy xavf")
    def top_hazard(self, obj):
        top = obj.top_hazards(1)
        return top[0]["label"] if top else "—"

    @admin.display(description="Prognozlar")
    def prediction_count(self, obj):
        return obj.predictions.count()


class ChatInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ("role", "content", "created_at")
    can_delete = True


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ("id", "region", "user", "horizon_years", "score_badge", "confidence", "source", "created_at")
    list_filter = ("level", "source", "horizon_years", "region", "created_at")
    search_fields = ("region__name", "user__username", "summary")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "hazard_table")
    inlines = [ChatInline]
    list_per_page = 25
    fieldsets = (
        ("Soʻrov", {"fields": ("user", "region", "horizon_years", "hazards", "notes")}),
        ("Natija", {"fields": ("overall_score", "level", "confidence", "summary", "hazard_table")}),
        ("Tafsilotlar", {"fields": ("scores", "timeline", "drivers", "recommendations", "satellite_sources")}),
        ("Meta", {"fields": ("source", "model_name", "created_at")}),
    )

    @admin.display(description="Xavf", ordering="overall_score")
    def score_badge(self, obj):
        return badge(f"{obj.overall_score:.0f} · {obj.get_level_display()}", obj.color)

    @admin.display(description="Xavf turlari")
    def hazard_table(self, obj):
        rows = "".join(
            format_html(
                '<div style="display:flex;align-items:center;gap:10px;margin:4px 0">'
                '<span style="width:170px">{}</span>'
                '<span style="flex:0 0 220px;height:8px;background:#33415555;border-radius:4px;overflow:hidden">'
                '<span style="display:block;height:100%;width:{}%;background:{}"></span></span><b>{}</b></div>',
                r["label"], r["score"], r["color"], r["score"])
            for r in obj.hazard_rows()
        )
        return mark_safe(rows) if rows else "—"  # each row already escaped by format_html


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("prediction", "role", "short", "created_at")
    list_filter = ("role",)

    @admin.display(description="Xabar")
    def short(self, obj):
        return obj.content[:90]
