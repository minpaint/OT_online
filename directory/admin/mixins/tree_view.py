from django.contrib import admin
from django.db.models import Q
from typing import Dict, Any, List


class TreeViewMixin:
    """
    🌳 Миксин для древовидного отображения в админке
    """

    def get_tree_data(self, request) -> Dict[str, Any]:
        """
        📊 Формирование древовидной структуры данных
        """
        # Получаем queryset с учетом прав доступа
        queryset = self.get_queryset(request)

        # Оптимизация запросов
        queryset = self._optimize_queryset(queryset)

        # Структура дерева
        tree = {}

        # Получаем настройки полей
        fields = self.tree_settings['fields']
        org_field = fields['organization_field']
        sub_field = fields['subdivision_field']
        dept_field = fields['department_field']

        # Получаем все организации
        organizations = set(getattr(obj, org_field) for obj in queryset if getattr(obj, org_field))

        # Формируем структуру дерева
        for org in organizations:
            if org not in tree:
                tree[org] = {
                    'items': [],
                    'subdivisions': {}
                }

            # Фильтруем объекты для текущей организации
            org_objects = [obj for obj in queryset if getattr(obj, org_field) == org]

            for obj in org_objects:
                sub = getattr(obj, sub_field)
                dept = getattr(obj, dept_field)

                # Объекты без подразделения и отдела
                if not sub and not dept:
                    if not self.tree_settings['display_rules']['hide_no_subdivision_no_department']:
                        tree[org]['items'].append(obj)
                    continue

                # Объекты с подразделением
                if sub:
                    if sub not in tree[org]['subdivisions']:
                        tree[org]['subdivisions'][sub] = {
                            'items': [],
                            'departments': {}
                        }

                    if dept:
                        # Объекты с отделом
                        if dept not in tree[org]['subdivisions'][sub]['departments']:
                            tree[org]['subdivisions'][sub]['departments'][dept] = []
                        tree[org]['subdivisions'][sub]['departments'][dept].append(obj)
                    else:
                        # Объекты только с подразделением
                        tree[org]['subdivisions'][sub]['items'].append(obj)
                else:
                    # Объекты без подразделения, но с отделом
                    if 'no_subdivision' not in tree[org]['subdivisions']:
                        tree[org]['subdivisions']['no_subdivision'] = {
                            'items': [],
                            'departments': {}
                        }
                    if dept:
                        if dept not in tree[org]['subdivisions']['no_subdivision']['departments']:
                            tree[org]['subdivisions']['no_subdivision']['departments'][dept] = []
                        tree[org]['subdivisions']['no_subdivision']['departments'][dept].append(obj)

        # Удаляем пустые ветки если включена соответствующая настройка
        if self.tree_settings['display_rules']['hide_empty_branches']:
            tree = self._remove_empty_branches(tree)

        return tree

    def _remove_empty_branches(self, tree):
        """
        🗑️ Удаление пустых веток дерева
        """
        result = {}
        for org, org_data in tree.items():
            # Проверяем есть ли данные в организации
            has_items = bool(org_data['items'])
            has_subdivisions = False

            # Проверяем подразделения
            subdivisions = {}
            for sub, sub_data in org_data['subdivisions'].items():
                # Проверяем есть ли данные в подразделении
                if sub_data['items'] or sub_data['departments']:
                    has_subdivisions = True
                    subdivisions[sub] = sub_data

            if has_items or has_subdivisions:
                result[org] = {
                    'items': org_data['items'],
                    'subdivisions': subdivisions
                }

        return result

    def _optimize_queryset(self, queryset):
        """
        🚀 Оптимизация запросов через select_related
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
        👁️ Переопределение отображения списка
        """
        extra_context = extra_context or {}
        extra_context.update({
            'tree': self.get_tree_data(request),
            'tree_settings': self.tree_settings
        })
        return super().changelist_view(request, extra_context)