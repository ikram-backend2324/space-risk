from django.conf import settings


def site(request):
    return {
        "SITE_NAME": "SPACE RISK",
        "SITE_TAGLINE": "Hududning kelajakdagi xavfini oldindan aytuvchi AI",
        "AI_ONLINE": bool(settings.OPENROUTER_API_KEY),
    }
