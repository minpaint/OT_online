#!/usr/bin/env python
"""Скрипт для проверки и настройки пунктов меню для пользователя otdel"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from django.contrib.auth.models import User
from directory.models import MenuItem, Profile

# Получаем пользователя
try:
    user = User.objects.get(username='otdel')
    print(f"Пользователь: {user.username}")
    print(f"Суперпользователь: {user.is_superuser}")

    # Проверяем профиль
    if hasattr(user, 'profile'):
        profile = user.profile
        print(f"Профиль: {profile}")

        current_items = list(profile.visible_menu_items.all())
        print(f"\nТекущие пункты меню ({len(current_items)}):")
        if current_items:
            for item in current_items:
                print(f"  - {item.icon} {item.name}")
        else:
            print("  (пусто - видны ВСЕ пункты)")
    else:
        print("Профиль: НЕТ")

    # Показываем все доступные пункты
    print("\n" + "="*60)
    print("Все доступные пункты меню в базе:")
    print("="*60)

    sidebar_items = MenuItem.objects.filter(is_active=True, location='sidebar').order_by('order')
    print("\nБоковое меню (sidebar):")
    for item in sidebar_items:
        separator = " [РАЗДЕЛИТЕЛЬ]" if item.is_separator else ""
        url = item.url_name or item.url or '#'
        print(f"  {item.order:2d}. {item.icon} {item.name:30s} -> {url}{separator}")

    top_items = MenuItem.objects.filter(is_active=True, location='top').order_by('order')
    print("\nВерхнее меню (top):")
    for item in top_items:
        url = item.url_name or item.url or '#'
        print(f"  {item.order:2d}. {item.icon} {item.name:30s} -> {url}")

except User.DoesNotExist:
    print("Пользователь 'otdel' не найден!")
