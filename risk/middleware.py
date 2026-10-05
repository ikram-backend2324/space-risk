from django.utils import translation

from . import i18n


class LanguageMiddleware:
    """Picks the UI language: ?lang= → cookie → Accept-Language → Uzbek."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        lang = (
            i18n.normalize(request.GET.get("lang"))
            or i18n.normalize(request.COOKIES.get(i18n.COOKIE))
            or i18n.from_accept_language(request.META.get("HTTP_ACCEPT_LANGUAGE"))
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
        translation.deactivate()
        return response
