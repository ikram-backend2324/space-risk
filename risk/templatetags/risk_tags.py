from django import template

from .. import i18n
from ..hazards import LEVEL_COLORS, level_for, level_label as _level_label

register = template.Library()


@register.simple_tag
def t(key, **params):
    """{% t "key" name=value %} — translated UI string in the active language."""
    return i18n.t(key, **params)


@register.filter
def level_color(score):
    try:
        return LEVEL_COLORS[level_for(float(score))]
    except (TypeError, ValueError):
        return "#64748b"


@register.filter
def level_label(score):
    try:
        return _level_label(level_for(float(score)))
    except (TypeError, ValueError):
        return ""


@register.filter
def priority_label(code):
    from ..hazards import priority_label as _p
    return _p(code)


@register.filter
def ago(dt):
    return i18n.ago(dt)


@register.filter
def years(n):
    return i18n.years(int(n))


@register.filter
def num(value):
    """Thousands separated by a thin space: 166 590."""
    try:
        return f"{int(value):,}".replace(",", " ")
    except (TypeError, ValueError):
        return value


@register.filter
def mln(value):
    try:
        text = f"{int(value) / 1e6:.2f}"
    except (TypeError, ValueError):
        return "—"
    return text if i18n.get_lang() == "en" else text.replace(".", ",")


@register.filter
def get_item(d, key):
    return d.get(key) if hasattr(d, "get") else None
