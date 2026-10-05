from django import template

from ..hazards import LEVEL_COLORS, LEVEL_LABELS, level_for

register = template.Library()


@register.filter
def level_color(score):
    try:
        return LEVEL_COLORS[level_for(float(score))]
    except (TypeError, ValueError):
        return "#64748b"


@register.filter
def level_label(score):
    try:
        return LEVEL_LABELS[level_for(float(score))]
    except (TypeError, ValueError):
        return ""


@register.filter
def get_item(d, key):
    return d.get(key) if hasattr(d, "get") else None


@register.filter
def mln(value):
    try:
        return f"{int(value) / 1e6:.2f}"
    except (TypeError, ValueError):
        return "—"
