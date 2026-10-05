from django.conf import settings

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
    }
