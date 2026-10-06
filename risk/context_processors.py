from django.conf import settings
from django.utils.functional import SimpleLazyObject

from . import i18n


def site(request):
    lang = getattr(request, "LANG", i18n.get_lang())
    return {
        "SITE_NAME": "SPACE RISK",
        "SITE_TAGLINE": i18n.t("site.tagline", lang),
        "AI_ONLINE": bool(settings.OPENROUTER_API_KEY),
        "LANG": lang,
        "LANGS": i18n.LANGUAGES,
        "LANG_SHORT": dict((c, s) for c, _, s in i18n.LANGUAGES)[lang],
        "JS_I18N": i18n.js_catalog(lang),
        "TELEGRAM_BOT_URL": settings.TELEGRAM_BOT_URL,
        "TELEGRAM_BOT_NAME": "@" + settings.TELEGRAM_BOT_URL.rstrip("/").rsplit("/", 1)[-1],
        "APK_VERSION": settings.ANDROID_APK_VERSION,
        "APK_SIZE_MB": SimpleLazyObject(_apk_size),
    }


def _apk_size():
    try:
        return f"{settings.ANDROID_APK_PATH.stat().st_size / 1048576:.1f}"
    except OSError:
        return "—"
