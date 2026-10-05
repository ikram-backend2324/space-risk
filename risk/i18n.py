"""
Lightweight 4-language support: Uzbek (uz), English (en), Russian (ru), Karakalpak (kaa).

Django's gettext has no Karakalpak catalog and would need GNU gettext on Render,
so UI strings live in Python dictionaries (``locale_ui.py`` / ``locale_content.py``)
and the active language is tracked per request by ``LanguageMiddleware``.
"""
from asgiref.local import Local
from django.utils import timezone
from django.utils.safestring import mark_safe

LANGUAGES = [
    ("uz", "Oʻzbekcha", "UZ"),
    ("en", "English", "EN"),
    ("ru", "Русский", "RU"),
    ("kaa", "Qaraqalpaqsha", "QQ"),
]
CODES = [code for code, _, _ in LANGUAGES]
DEFAULT = "uz"
COOKIE = "sr_lang"

# Language names used when instructing the AI model.
AI_LANGUAGE = {
    "uz": "Uzbek (Latin script, e.g. 'xavf', 'hudud', 'prognoz')",
    "en": "English",
    "ru": "Russian (Cyrillic script)",
    "kaa": (
        "Karakalpak (Qaraqalpaq tili) in the official Latin alphabet with the letters "
        "á, ǵ, ı, ń, ó, ú, w, y — e.g. 'qáwip' (risk), 'boljaw' (forecast), 'aymaq' (region), "
        "'wálayat' (province), 'jasalma joldas' (satellite), 'usınıs' (recommendation). "
        "Do NOT write in Uzbek or Kazakh"
    ),
}

_state = Local()


def get_lang():
    return getattr(_state, "lang", DEFAULT)


def set_lang(lang):
    _state.lang = lang if lang in CODES else DEFAULT


def normalize(code):
    if not code:
        return None
    code = code.strip().lower().replace("_", "-")
    if code in CODES:
        return code
    base = code.split("-")[0]
    if base in ("kaa", "qq"):
        return "kaa"
    return base if base in CODES else None


def from_accept_language(header):
    for part in (header or "").split(","):
        lang = normalize(part.split(";")[0])
        if lang:
            return lang
    return None


def t(key, lang=None, **params):
    """Translate a UI key. Keys ending in ``_html`` are returned as safe HTML."""
    from .locale_ui import UI

    lang = lang or get_lang()
    entry = UI.get(key)
    if entry is None:
        return key
    text = entry.get(lang) or entry.get(DEFAULT) or key
    if params:
        try:
            text = text.format(**params)
        except (KeyError, IndexError, ValueError):
            pass
    return mark_safe(text) if key.endswith("_html") else text


def lower_first(text, lang=None):
    """Lower-case the first letter (keeps proper nouns/acronyms inside intact).

    Karakalpak's capital of dotless ``ı`` is ``Í``; Python would lower it to ``í``.
    """
    if not text:
        return text
    lang = lang or get_lang()
    first = text[0]
    if lang == "kaa" and first == "Í":
        first = "ı"
    else:
        first = first.lower()
    return first + text[1:]


def join_and(items, lang=None):
    items = list(items)
    if len(items) < 2:
        return "".join(items)
    word = t("word.and", lang)
    return ", ".join(items[:-1]) + f" {word} " + items[-1]


def years(n, lang=None):
    lang = lang or get_lang()
    if lang == "en":
        return f"{n} year" if n == 1 else f"{n} years"
    if lang == "ru":
        if n % 10 == 1 and n % 100 != 11:
            return f"{n} год"
        if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
            return f"{n} года"
        return f"{n} лет"
    if lang == "kaa":
        return f"{n} jıl"
    return f"{n} yil"


def ago(dt, lang=None):
    if not dt:
        return ""
    seconds = int((timezone.now() - dt).total_seconds())
    if seconds < 60:
        return t("ago.now", lang)
    if seconds < 3600:
        return t("ago.min", lang, n=seconds // 60)
    if seconds < 86400:
        return t("ago.hour", lang, n=seconds // 3600)
    if seconds < 30 * 86400:
        return t("ago.day", lang, n=seconds // 86400)
    return timezone.localtime(dt).strftime("%d.%m.%Y")


def js_catalog(lang=None):
    from .locale_ui import UI

    lang = lang or get_lang()
    return {k[3:]: v.get(lang) or v.get(DEFAULT) for k, v in UI.items() if k.startswith("js.")}
