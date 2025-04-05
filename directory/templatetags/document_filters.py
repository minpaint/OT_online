# D:\YandexDisk\OT_online\directory\templatetags\document_filters.py
from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Фильтр для получения значения из словаря по ключу в шаблоне.

    Пример использования:
    {{ dictionary|get_item:key }}

    Args:
        dictionary: Словарь, из которого нужно получить значение
        key: Ключ, по которому нужно получить значение

    Returns:
        Значение из словаря по указанному ключу, или сам ключ, если значение не найдено
    """
    return dictionary.get(key, key)


@register.filter
def get_document_type_display(document_type):
    """
    Фильтр для получения отображаемого названия типа документа.

    Пример использования:
    {{ document_type|get_document_type_display }}

    Args:
        document_type: Строковый код типа документа

    Returns:
        Отображаемое название типа документа
    """
    document_types = {
        'all_orders': '📝 Распоряжения о стажировке',
        'knowledge_protocol': '📋 Протокол проверки знаний по охране труда',
        'doc_familiarization': '📝 Лист ознакомления с документами',
        'siz_card': '🛡️ Карточка учета СИЗ',
    }
    return document_types.get(document_type, document_type)


@register.filter
def has_missing_data(document_data):
    """
    Фильтр для проверки наличия недостающих данных в документе.

    Пример использования:
    {% if document_data|has_missing_data %}...{% endif %}

    Args:
        document_data: Словарь с данными документа

    Returns:
        True, если в документе есть недостающие данные, иначе False
    """
    return document_data.get('has_missing_data', False)


@register.filter
def get_missing_data(document_data):
    """
    Фильтр для получения списка недостающих данных в документе.

    Пример использования:
    {% for item in document_data|get_missing_data %}...{% endfor %}

    Args:
        document_data: Словарь с данными документа

    Returns:
        Список недостающих данных или пустой список, если данных нет
    """
    return document_data.get('missing_data', [])