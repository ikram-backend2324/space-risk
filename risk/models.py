from django.conf import settings
from django.db import models
from django.urls import reverse

from .hazards import HAZARDS, HORIZONS, LEVEL_CHOICES, LEVEL_COLORS, hazard, level_for, level_label, region_text
from .i18n import CODES as LANG_CODES


class Region(models.Model):
    name = models.CharField("Nomi", max_length=120)
    slug = models.SlugField(unique=True)
    center = models.CharField("Markazi", max_length=80, blank=True)
    lat = models.FloatField("Kenglik")
    lng = models.FloatField("Uzunlik")
    area_km2 = models.PositiveIntegerField("Maydoni, km²", default=0)
    population = models.PositiveIntegerField("Aholisi", default=0)
    description = models.TextField("Tavsif", blank=True)
    baseline = models.JSONField("Bazaviy xavf indekslari", default=dict,
                                help_text="Xavf turi kodi → 0..100 indeks")
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "Hudud"
        verbose_name_plural = "Hududlar"

    def __str__(self):
        return self.name

    @property
    def display_name(self):
        """Region name in the active UI language."""
        return region_text(self.slug, self.name, self.description)[0]

    @property
    def display_description(self):
        return region_text(self.slug, self.name, self.description)[1]

    @property
    def level_label(self):
        return level_label(self.level)

    @property
    def composite(self):
        vals = [v for v in self.baseline.values() if isinstance(v, (int, float))]
        if not vals:
            return 0
        # Weighted toward the strongest hazards — a region is as risky as its worst threats.
        top = sorted(vals, reverse=True)[:3]
        return round(0.6 * sum(top) / len(top) + 0.4 * sum(vals) / len(vals))

    @property
    def level(self):
        return level_for(self.composite)

    @property
    def color(self):
        return LEVEL_COLORS[self.level]

    def top_hazards(self, n=3):
        items = sorted(self.baseline.items(), key=lambda kv: kv[1], reverse=True)[:n]
        return [{**hazard(k), "score": v} for k, v in items if k in HAZARDS]

    def as_map_dict(self):
        return {
            "name": self.display_name, "slug": self.slug, "lat": self.lat, "lng": self.lng,
            "population": self.population, "score": self.composite, "level": self.level,
            "color": self.color, "top": [h["label"] for h in self.top_hazards(2)],
        }


class Prediction(models.Model):
    SOURCE_CHOICES = [("ai", "AI (OpenRouter)"), ("engine", "Ichki model")]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="predictions")
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name="predictions", verbose_name="Hudud")
    horizon_years = models.PositiveSmallIntegerField("Prognoz muddati", choices=HORIZONS, default=5)
    hazards = models.JSONField("Tahlil qilingan xavflar", default=list)
    notes = models.TextField("Qoʻshimcha kontekst", blank=True)

    overall_score = models.FloatField("Umumiy xavf", default=0)
    level = models.CharField("Daraja", max_length=12, choices=LEVEL_CHOICES, default="low")
    confidence = models.PositiveSmallIntegerField("Ishonchlilik, %", default=70)
    summary = models.TextField("Xulosa", blank=True)
    scores = models.JSONField("Xavf turlari boʻyicha ball", default=dict)
    timeline = models.JSONField("Vaqt boʻyicha dinamika", default=list)
    drivers = models.JSONField("Asosiy omillar", default=list)
    recommendations = models.JSONField("Tavsiyalar", default=list)
    satellite_sources = models.JSONField("Sunʼiy yoʻldosh manbalari", default=list)

    language = models.CharField("Til", max_length=5, choices=[(c, c) for c in LANG_CODES], default="uz")
    translations = models.JSONField("AI tarjimalari", default=dict, blank=True,
                                    help_text="Til kodi → tarjima qilingan xulosa, omillar va tavsiyalar")
    source = models.CharField("Manba", max_length=10, choices=SOURCE_CHOICES, default="engine")
    model_name = models.CharField("Model", max_length=120, blank=True)
    created_at = models.DateTimeField("Yaratilgan", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Prognoz"
        verbose_name_plural = "Prognozlar"

    def __str__(self):
        return f"{self.region} · {self.horizon_years} yil · {self.overall_score:.0f}"

    def get_absolute_url(self):
        return reverse("risk:detail", args=[self.pk])

    @property
    def color(self):
        return LEVEL_COLORS.get(self.level, "#64748b")

    @property
    def level_label(self):
        return level_label(self.level)

    @property
    def target_year(self):
        return self.created_at.year + self.horizon_years

    def hazard_rows(self):
        rows = []
        for code, score in sorted(self.scores.items(), key=lambda kv: kv[1], reverse=True):
            if code not in HAZARDS:
                continue
            lvl = level_for(score)
            rows.append({**hazard(code), "score": round(score), "level": lvl,
                         "level_label": level_label(lvl), "level_color": LEVEL_COLORS[lvl]})
        return rows


class ChatMessage(models.Model):
    ROLE_CHOICES = [("user", "Foydalanuvchi"), ("assistant", "AI")]

    prediction = models.ForeignKey(Prediction, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "AI suhbat xabari"
        verbose_name_plural = "AI suhbat xabarlari"

    def __str__(self):
        return f"{self.get_role_display()}: {self.content[:60]}"
