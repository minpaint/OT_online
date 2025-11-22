# directory/templatetags/menu_tags.py
"""
Теги и фильтры для работы с системой меню и правами доступа.
"""
from django import template
from directory.models import MenuItem

register = template.Library()


@register.simple_tag(takes_context=True)
def get_visible_menu_items(context, location='sidebar'):
    """
    Возвращает список видимых пунктов меню для текущего пользователя.

    Args:
        context: Контекст шаблона
        location: Расположение меню ('sidebar', 'top', 'both')

    Returns:
        QuerySet активных пунктов меню, видимых для пользователя
    """
    request = context.get('request')
    if not request:
        return MenuItem.objects.none()

    user = request.user

    # Получаем все активные пункты меню для указанного расположения
    if location == 'both':
        menu_items = MenuItem.objects.filter(is_active=True)
    else:
        menu_items = MenuItem.objects.filter(
            is_active=True,
            location__in=[location, 'both']
        )

    # Фильтруем по видимости для пользователя
    visible_items = []
    for item in menu_items.order_by('order', 'name'):
        if item.is_visible_for_user(user):
            visible_items.append(item)

    return visible_items


@register.filter
def is_menu_visible(menu_item, user):
    """
    Проверяет, виден ли пункт меню для пользователя.

    Args:
        menu_item: Объект MenuItem или строка с URL name
        user: Объект User

    Returns:
        bool: True если пункт виден
    """
    if isinstance(menu_item, str):
        # Если передана строка (url_name), находим соответствующий MenuItem
        try:
            menu_item = MenuItem.objects.get(url_name=menu_item, is_active=True)
        except MenuItem.DoesNotExist:
            # Если пункт меню не найден в базе, считаем его видимым (обратная совместимость)
            return True

    if not isinstance(menu_item, MenuItem):
        return True

    return menu_item.is_visible_for_user(user)


@register.simple_tag
def check_url_visibility(user, url_name):
    """
    Проверяет видимость URL по его имени.

    Args:
        user: Объект User
        url_name: Django URL name

    Returns:
        bool: True если URL виден пользователю
    """
    try:
        menu_item = MenuItem.objects.get(url_name=url_name, is_active=True)
        return menu_item.is_visible_for_user(user)
    except MenuItem.DoesNotExist:
        # Если пункт не найден в MenuItem, считаем его видимым
        return True
