from directory.admin.mixins.tree_view import TreeViewMixin


class CommissionTreeViewMixin(TreeViewMixin):
    """
    Миксин для отображения комиссий в виде дерева с участниками.
    """
    change_list_template = "admin/directory/commission/change_list_tree.html"

    # Переопределяем настройки дерева для комиссий
    tree_settings = {
        'icons': {
            'organization': '🏢',
            'subdivision': '🏭',
            'department': '📂',
            'item': '🛡️',  # Иконка для комиссий по умолчанию
            'ot': '🛡️',  # Иконки для разных типов комиссий
            'eb': '⚡',
            'pb': '🔥',
            'other': '📋'
        },
        'fields': {
            'name_field': 'name',
            'organization_field': 'organization',
            'subdivision_field': 'subdivision',
            'department_field': 'department',
        },
        'display_rules': {
            'hide_empty_branches': False,
            'hide_no_subdivision_no_department': False
        }
    }

    def get_tree_data(self, request):
        """
        Переопределяем метод формирования дерева, чтобы включить информацию
        об участниках комиссии.
        """
        # Получаем базовое дерево из родительского метода
        tree = super().get_tree_data(request)

        # Обогащаем структуру дерева информацией об участниках комиссий
        self._enrich_tree_with_members(tree)

        return tree

    def _enrich_tree_with_members(self, tree):
        """
        Дополняет дерево информацией о составе комиссий.
        """
        # Проходим по всем организациям в дереве
        for org_data in tree.values():
            # Обрабатываем комиссии на уровне организации
            for item in org_data['items']:
                self._add_members_to_item(item)

            # Проходим по подразделениям
            for sub_data in org_data['subdivisions'].values():
                # Обрабатываем комиссии на уровне подразделения
                for item in sub_data['items']:
                    self._add_members_to_item(item)

                # Проходим по отделам
                for dept_data in sub_data['departments'].values():
                    # Обрабатываем комиссии на уровне отдела
                    for item in dept_data['items']:
                        self._add_members_to_item(item)

    def _add_members_to_item(self, item):
        """
        Добавляет информацию об участниках к комиссии.
        """
        obj = item['object']
        # Проверяем, что объект является комиссией
        if hasattr(obj, 'members'):
            # Получаем активных участников комиссии с prefetch_related
            members = obj.members.filter(is_active=True).select_related('employee')

            # Группируем участников по ролям
            roles = {
                'chairman': [],
                'secretary': [],
                'member': []
            }

            for member in members:
                elif hasattr(member.employee, 'position_name'):
                    position = member.employee.position_name
                elif hasattr(member.employee, 'job_title'):
                    position = member.employee.job_title

                roles[member.role].append({
                    'name': getattr(member.employee, 'full_name_nominative', str(member.employee)),
                    'role': member.get_role_display(),
                    'role_code': member.role
                })

            # Добавляем информацию об участниках в элемент дерева
            item['members'] = {
                'chairman': roles['chairman'],
                'secretary': roles['secretary'],
                'members': roles['member'],
                'total': len(members)
            }

            # Добавляем тип комиссии и статус активности
            item['commission_type'] = obj.commission_type
            item['is_active'] = obj.is_active

    def _optimize_queryset(self, queryset):
        """
        Оптимизируем запросы, добавляя prefetch_related для участников.
        """
        qs = super()._optimize_queryset(queryset)