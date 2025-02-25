"""
🌳 Единый миксин для древовидного отображения в админке.

Логика формирования дерева: Организация → Подразделение → Отдел → Объект.

Если какое-либо поле не применяется (например, у Department нет department),
его можно задать как None. Миксин проверяет наличие поля перед вызовом getattr.
"""

class TreeViewMixin:
    # 🚩 Базовый шаблон для отображения дерева (можно переопределять в каждом Admin-классе)
    change_list_template = "admin/directory/position/change_list_tree.html"

    # ⚙️ Настройки по умолчанию (в Admin-классах их можно переопределять)
    tree_settings = {
        'icons': {
            'organization': '🏢',
            'subdivision': '🏭',
            'department': '📂',
            'item': '💼',
            'no_subdivision': '🏗️',
            'no_department': '📁'
        },
        'fields': {
            # Имя поля, которое будет отображаться как название объекта (например, 'position_name' или 'name')
            'name_field': 'name',
            'organization_field': 'organization',
            'subdivision_field': 'subdivision',
            'department_field': 'department',  # Если поле не применяется, задайте None
        },
        'display_rules': {
            'hide_empty_branches': False,
            'hide_no_subdivision_no_department': False
        }
    }

    def changelist_view(self, request, extra_context=None):
        """
        👁️ Переопределяем стандартный changelist_view,
        чтобы передать в контекст готовое дерево и настройки.
        """
        extra_context = extra_context or {}
        tree = self.get_tree_data(request)
        extra_context.update({
            'tree': tree,
            'tree_settings': self.tree_settings,
        })
        return super().changelist_view(request, extra_context)

    def get_tree_data(self, request):
        """
        📊 Формирует иерархическую структуру (словарь) дерева.
        Структура выглядит так:
        {
            org_obj: {
                'name': ...,
                'items': [ ... ],  # Объекты без subdivision
                'subdivisions': {
                    sub_obj: {
                        'name': ...,
                        'items': [ ... ],  # Объекты без department
                        'departments': {
                            dept_obj: {
                                'name': ...,
                                'items': [ ... ]
                            },
                            ...
                        }
                    },
                    ...
                }
            },
            ...
        }
        """
        # Получаем QuerySet из стандартного метода get_queryset
        qs = self.get_queryset(request)
        # Оптимизируем запрос, используя select_related для заданных полей
        qs = self._optimize_queryset(qs)

        tree = {}
        fields = self.tree_settings['fields']
        # Получаем названия полей из настроек; если поле не применяется, то значение будет None
        org_field = fields.get('organization_field')
        sub_field = fields.get('subdivision_field')
        dept_field = fields.get('department_field')
        name_field = fields.get('name_field')

        # Проходимся по объектам QuerySet
        for obj in qs:
            # Получаем организацию, если поле задано
            org = getattr(obj, org_field) if org_field else None
            if not org:
                continue  # Если у объекта нет организации, пропускаем его

            # Получаем subdivision, если задано
            sub = getattr(obj, sub_field) if sub_field else None
            # Получаем department, если задано
            dept = getattr(obj, dept_field) if dept_field else None

            # Используем метод tree_display_name, если он существует
            if hasattr(obj, 'tree_display_name'):
                item_name = obj.tree_display_name()
            else:
                # Иначе получаем название объекта из заданного поля или используем str(obj)
                item_name = getattr(obj, name_field, str(obj)) if name_field else str(obj)

            # Формируем словарь данных для объекта (лист дерева)
            item_data = {
                'name': item_name,
                'object': obj,
                'pk': obj.pk
            }

            # 1️⃣ Организация
            if org not in tree:
                tree[org] = {
                    # Предполагаем, что у организации есть атрибут short_name_ru; иначе используем str(org)
                    'name': getattr(org, 'short_name_ru', str(org)),
                    'items': [],
                    'subdivisions': {}
                }

            # 2️⃣ Если subdivision не задан, добавляем объект сразу к организации
            if not sub:
                tree[org]['items'].append(item_data)
                continue

            # 3️⃣ Подразделение
            if sub not in tree[org]['subdivisions']:
                tree[org]['subdivisions'][sub] = {
                    'name': getattr(sub, 'name', str(sub)),
                    'items': [],
                    'departments': {}
                }

            # 4️⃣ Если department не задан, добавляем объект к подразделению
            if not dept:
                tree[org]['subdivisions'][sub]['items'].append(item_data)
                continue

            # 5️⃣ Отдел
            if dept not in tree[org]['subdivisions'][sub]['departments']:
                tree[org]['subdivisions'][sub]['departments'][dept] = {
                    'name': getattr(dept, 'name', str(dept)),
                    'items': []
                }

            tree[org]['subdivisions'][sub]['departments'][dept]['items'].append(item_data)

        return tree

    def _optimize_queryset(self, queryset):
        """
        🚀 Оптимизирует запрос, используя select_related для указанных полей.
        Фильтрует поля, равные None, чтобы избежать ошибок.
        """
        fields = self.tree_settings['fields']
        related_fields = [
            fields.get('organization_field'),
            fields.get('subdivision_field'),
            fields.get('department_field')
        ]
        # Убираем значения None
        related_fields = [field for field in related_fields if field is not None]

        return queryset.select_related(*related_fields)