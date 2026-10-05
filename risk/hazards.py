"""Static reference data: hazard types, risk levels, Uzbekistan regions."""

# code -> label, lucide icon, colour, annual trend (index points / year under climate change),
#         satellite sources used to observe it
HAZARDS = {
    "seismic": {
        "label": "Zilzila",
        "icon": "activity",
        "color": "#f43f5e",
        "trend": 0.0,
        "sources": ["Sentinel-1 InSAR", "GNSS tarmogʻi"],
        "desc": "Seysmik faollik va yer qobigʻi deformatsiyasi",
    },
    "flood": {
        "label": "Sel va toshqin",
        "icon": "waves",
        "color": "#3b82f6",
        "trend": 0.45,
        "sources": ["Sentinel-1 SAR", "GPM yogʻingarchilik"],
        "desc": "Togʻ sellari, daryo toshqinlari, suv omborlari xavfi",
    },
    "drought": {
        "label": "Qurgʻoqchilik",
        "icon": "sun",
        "color": "#f59e0b",
        "trend": 0.9,
        "sources": ["MODIS NDVI", "SMAP tuproq namligi"],
        "desc": "Yogʻin tanqisligi va oʻsimliklar stressi",
    },
    "heatwave": {
        "label": "Issiqlik toʻlqini",
        "icon": "thermometer-sun",
        "color": "#ef4444",
        "trend": 1.1,
        "sources": ["Landsat-9 TIRS", "MODIS LST"],
        "desc": "Ekstremal harorat va shahar issiqlik orollari",
    },
    "landslide": {
        "label": "Koʻchki va surilish",
        "icon": "mountain",
        "color": "#a16207",
        "trend": 0.3,
        "sources": ["Sentinel-1 InSAR", "SRTM DEM"],
        "desc": "Yonbagʻir surilishi, qor koʻchkilari",
    },
    "dust": {
        "label": "Chang-tuz boʻronlari",
        "icon": "wind",
        "color": "#d97706",
        "trend": 0.7,
        "sources": ["Sentinel-5P", "MODIS AOD"],
        "desc": "Orol tubidan koʻtarilgan tuzli changlar",
    },
    "water": {
        "label": "Suv tanqisligi",
        "icon": "droplets",
        "color": "#06b6d4",
        "trend": 1.0,
        "sources": ["GRACE-FO", "Sentinel-2 suv yuzasi"],
        "desc": "Yer osti va yer usti suv zaxiralari kamayishi",
    },
    "air": {
        "label": "Havo ifloslanishi",
        "icon": "factory",
        "color": "#8b5cf6",
        "trend": 0.5,
        "sources": ["Sentinel-5P TROPOMI", "Yer usti stansiyalari"],
        "desc": "PM2.5, NO₂, SO₂ konsentratsiyalari",
    },
    "desertification": {
        "label": "Choʻllanish",
        "icon": "tent-tree",
        "color": "#ca8a04",
        "trend": 0.8,
        "sources": ["Landsat arxivi", "Sentinel-2 NDVI"],
        "desc": "Yer degradatsiyasi va shoʻrlanish",
    },
}

HAZARD_CHOICES = [(code, h["label"]) for code, h in HAZARDS.items()]

HORIZONS = [(1, "1 yil"), (5, "5 yil"), (10, "10 yil"), (25, "25 yil")]

LEVELS = [
    ("low", "Past", "#22c55e", 0),
    ("moderate", "Oʻrtacha", "#eab308", 35),
    ("high", "Yuqori", "#f97316", 55),
    ("critical", "Kritik", "#ef4444", 75),
]
LEVEL_CHOICES = [(code, label) for code, label, _, _ in LEVELS]
LEVEL_COLORS = {code: color for code, _, color, _ in LEVELS}
LEVEL_LABELS = {code: label for code, label, _, _ in LEVELS}


def level_for(score):
    current = LEVELS[0][0]
    for code, _, _, threshold in LEVELS:
        if score >= threshold:
            current = code
    return current


# name, slug, centre, lat, lng, area km², population, description, baseline indices
_H = ["seismic", "flood", "drought", "heatwave", "landslide", "dust", "water", "air", "desertification"]
_REGIONS = [
    ("Toshkent shahri", "toshkent-shahri", "Toshkent", 41.2995, 69.2401, 335, 3_040_000,
     "Poytaxt: yuqori aholi zichligi, seysmik faol zona (1966-yil zilzilasi), shahar issiqlik oroli.",
     [78, 35, 40, 72, 15, 40, 45, 80, 15]),
    ("Toshkent viloyati", "toshkent-viloyati", "Nurafshon", 41.0400, 69.3600, 15_300, 3_000_000,
     "Chatqol va Qurama togʻlari, Angren–Olmaliq sanoat zonasi, sel va koʻchki xavfi yuqori.",
     [70, 70, 45, 55, 75, 35, 40, 65, 25]),
    ("Andijon viloyati", "andijon", "Andijon", 40.7821, 72.3442, 4_300, 3_300_000,
     "Fargʻona vodiysining eng zich hududi, kuchli seysmik faollik.",
     [85, 60, 45, 60, 70, 30, 45, 50, 25]),
    ("Namangan viloyati", "namangan", "Namangan", 40.9983, 71.6726, 7_440, 3_000_000,
     "Togʻ oldi hududlari, sel oqimlari va koʻchkilar.",
     [75, 70, 50, 60, 65, 35, 50, 45, 35]),
    ("Fargʻona viloyati", "fargona", "Fargʻona", 40.3864, 71.7864, 6_760, 3_900_000,
     "Sanoat va qishloq xoʻjaligi markazi, seysmik va ekologik bosim.",
     [75, 60, 50, 65, 55, 40, 50, 60, 35]),
    ("Sirdaryo viloyati", "sirdaryo", "Guliston", 40.4897, 68.7842, 4_280, 900_000,
     "Mirzachoʻl tekisligi, shoʻrlanish, Sardoba suv ombori (2020) tajribasi.",
     [45, 55, 65, 70, 10, 45, 60, 35, 50]),
    ("Jizzax viloyati", "jizzax", "Jizzax", 40.1158, 67.8422, 21_180, 1_450_000,
     "Choʻl va togʻ oraligʻidagi hudud, suv tanqisligi oʻsmoqda.",
     [50, 50, 70, 70, 40, 45, 65, 35, 55]),
    ("Samarqand viloyati", "samarqand", "Samarqand", 39.6542, 66.9597, 16_770, 4_200_000,
     "Zarafshon vodiysi, tarixiy meros obyektlari, seysmik xavf.",
     [60, 55, 55, 65, 45, 35, 55, 50, 40]),
    ("Qashqadaryo viloyati", "qashqadaryo", "Qarshi", 38.8606, 65.7891, 28_570, 3_500_000,
     "Gaz sanoati (Muborak), issiq iqlim, sel xavfi togʻ hududlarida.",
     [50, 60, 70, 80, 55, 50, 70, 50, 60]),
    ("Surxondaryo viloyati", "surxondaryo", "Termiz", 37.2242, 67.2783, 20_100, 2_800_000,
     "Oʻzbekistonning eng issiq hududi, seysmik faol togʻlar.",
     [65, 65, 65, 90, 60, 55, 60, 40, 55]),
    ("Buxoro viloyati", "buxoro", "Buxoro", 39.7747, 64.4286, 40_320, 2_000_000,
     "Qizilqum choʻli chegarasi, Gazli zilzilalari (1976, 1984), suv tanqisligi.",
     [55, 25, 80, 80, 10, 70, 80, 45, 80]),
    ("Navoiy viloyati", "navoiy", "Navoiy", 40.1039, 65.3792, 110_990, 1_050_000,
     "Kon-metallurgiya markazi, keng choʻl hududlari.",
     [55, 25, 80, 75, 15, 70, 75, 55, 80]),
    ("Xorazm viloyati", "xorazm", "Urganch", 41.5500, 60.6333, 6_050, 1_950_000,
     "Amudaryo quyi oqimi, Orol inqirozi taʼsiri, shoʻrlanish.",
     [30, 45, 80, 75, 10, 80, 85, 45, 75]),
    ("Qoraqalpogʻiston Respublikasi", "qoraqalpogiston", "Nukus", 42.4600, 59.6000, 166_590, 2_000_000,
     "Orol dengizi ekologik falokati markazi: tuzli chang boʻronlari, choʻllanish.",
     [25, 40, 90, 80, 10, 95, 95, 60, 95]),
]

REGIONS = [
    {
        "name": name, "slug": slug, "center": center, "lat": lat, "lng": lng,
        "area_km2": area, "population": pop, "description": desc,
        "baseline": dict(zip(_H, base)), "order": i,
    }
    for i, (name, slug, center, lat, lng, area, pop, desc, base) in enumerate(_REGIONS)
]
