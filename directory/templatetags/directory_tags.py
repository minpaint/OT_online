# directory/templatetags/directory_tags.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Получает значение из словаря по ключу.
    Для использования в шаблоне.
    """
    return dictionary.get(key, '')