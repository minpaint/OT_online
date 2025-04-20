# directory/templatetags/equipment_tags.py
from django import template

register = template.Library()


@register.filter
def maintenance_state(days):
    """
    Возвращает класс CSS для подсветки дат ТО.

    Аргументы:
        days (int): Количество дней до следующего ТО. Может быть None.

    Возвращает:
        str: Класс CSS для подсветки:
            - "overdue" - просрочено (дни < 0)
            - "warning" - скоро (0 <= дни <= 7)
            - "ok" - норма (дни > 7)
            - "unknown" - неизвестно (дни is None)
    """
    if days is None:
        return 'unknown'
    if days < 0:
        return 'overdue'
    if days <= 7:
        return 'warning'
    return 'ok'