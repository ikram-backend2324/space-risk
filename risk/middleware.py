from django.utils import translation

from . import i18n


class LanguageMiddleware:
    """Picks the UI language: ?lang= → X-Lang header (mobile app / bot) → cookie → Uzbek.

    The browser's Accept-Language is deliberately ignored: many phones in Uzbekistan report
    Russian, and the site should open in Uzbek until the user picks a language.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from_query = i18n.normalize(request.GET.get("lang"))
        lang = (
            from_query
            or i18n.normalize(request.headers.get("X-Lang"))
            or i18n.normalize(request.COOKIES.get(i18n.COOKIE))
            or i18n.DEFAULT
        )
        if request.path.startswith("/admin/"):
            lang = "uz"
        i18n.set_lang(lang)
        request.LANG = lang
        # The admin's model names are Uzbek, so keep the whole admin in Uzbek.
        # (Django also has no Karakalpak catalog.)
        if request.path.startswith("/admin/") or lang == "kaa":
            translation.activate("uz")
        else:
            translation.activate(lang)
        response = self.get_response(request)
        response.headers.setdefault("Content-Language", lang)
        # A shared link like /?lang=ru keeps that language on the following pages too.
        if from_query and not request.path.startswith("/api/") and request.COOKIES.get(i18n.COOKIE) != from_query:
            response.set_cookie(i18n.COOKIE, from_query, max_age=365 * 24 * 3600, samesite="Lax")
        translation.deactivate()
        return response
