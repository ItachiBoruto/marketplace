from django import template

register = template.Library()


@register.filter
def to_bs(value, rate):
    if rate is None or value is None or value == "":
        return ""
    try:
        return f"{float(value) * float(rate):,.2f}"
    except (TypeError, ValueError):
        return ""
