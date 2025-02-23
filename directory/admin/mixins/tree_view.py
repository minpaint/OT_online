"""
🌳 Миксин для древовидного отображения в админке
"""

from django.contrib import admin
from django.db.models import Q
from typing import Dict, Any


class TreeViewMixin:
    change_list_template = "admin/directory/position/change_list_tree.html"

    tree_settings = {
        'icons': {
            'organization': '🏢',
            'subdivision': '🏭',
            'department': '📂',
            'position': '👔',
            'no_subdivision': '🏗️',
            'no_department': '📁'
        },
        'fields': {
            'name_field': 'position_name',
            'organization_field': 'organization',
            'subdivision_field': 'subdivision',
            'department_field': 'department',
        },
        'display_rules': {
            'hide_empty_branches': True,
            'hide_no_subdivision_no_department': True
        }
    }

    def get_tree_data(self, request) -> Dict[str, Any]:
        """
        📊 Формирование древовидной структуры данных
        """
        queryset = self.get_queryset(request)
        queryset = self._optimize_queryset(queryset)

        tree = {}
        fields = self.tree_settings['fields']

        for obj in queryset:
            org = getattr(obj, fields['organization_field'])
            if not org:
                continue

            # Инициализируем структуру для организации
            if org not in tree:
                tree[org] = {
                    'name': org.short_name_ru,  # используем short_name_ru для организации
                    'items': [],
                    'subdivisions': {}
                }

            sub = getattr(obj, fields['subdivision_field'])
            dept = getattr(obj, fields['department_field'])

            # Создаем данные для позиции
            position_data = {
                'name': obj.position_name,
                'object': obj,
                'pk': obj.pk  # Важно! Добавляем pk
            }

            # Если нет подразделения
            if not sub:
                tree[org]['items'].append(position_data)
                continue

            # Инициализируем структуру для подразделения
            if sub not in tree[org]['subdivisions']:
                tree[org]['subdivisions'][sub] = {
                    'name': sub.name,
                    'items': [],
                    'departments': {}
                }

            # Если нет отдела
            if not dept:
                tree[org]['subdivisions'][sub]['items'].append(position_data)
                continue

            # Добавляем должность в отдел
            if dept not in tree[org]['subdivisions'][sub]['departments']:
                tree[org]['subdivisions'][sub]['departments'][dept] = {
                    'name': dept.name,
                    'items': []
                }

            tree[org]['subdivisions'][sub]['departments'][dept]['items'].append(position_data)

        return tree

    def _optimize_queryset(self, queryset):
        """
        🚀 Оптимизация запросов
        """
        fields = self.tree_settings['fields']
        related_fields = [
            fields['organization_field'],
            fields['subdivision_field'],
            fields['department_field']
        ]
        return queryset.select_related(*related_fields)

    def changelist_view(self, request, extra_context=None):
        """
        👁️ Отображение списка
        """
        extra_context = extra_context or {}
        tree = self.get_tree_data(request)

        extra_context.update({
            'tree': tree,
            'tree_settings': self.tree_settings
        })
        return super().changelist_view(request, extra_context)