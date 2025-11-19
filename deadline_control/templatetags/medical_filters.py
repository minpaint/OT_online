# deadline_control/templatetags/medical_filters.py
from django import template

register = template.Library()


@register.filter
def abs_value(value):
    """Возвращает абсолютное значение числа"""
    try:
        return abs(int(value))
    except (ValueError, TypeError):
        return 0
