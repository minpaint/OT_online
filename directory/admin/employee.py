from django.contrib import admin
from directory.models import Employee
from directory.forms.employee import EmployeeForm

# 👇 Подключаем наш миксин
from directory.admin.mixins.tree_view import TreeViewMixin

@admin.register(Employee)
class EmployeeAdmin(TreeViewMixin, admin.ModelAdmin):
    """
    👤 Админ-класс для модели Employee.
    Здесь используем TreeViewMixin, чтобы выводить древовидную структуру
    (Организация → Подразделение → Отдел → Сотрудник)
    и при этом отображать 'ФИО – должность' в колонке "Наименование".
    """
    form = EmployeeForm

    # Шаблон для дерева (например, "change_list_tree.html")
    change_list_template = "admin/directory/employee/change_list_tree.html"

    # Настройки дерева
    tree_settings = {
        'icons': {
            'organization': '🏢',
            'subdivision': '🏭',
            'department': '📂',
            'employee': '👤',  # можно не использовать напрямую, если выводим tree_settings.icons.item
            'no_subdivision': '🏗️',
            'no_department': '📁'
        },
        'fields': {
            # ВАЖНО: теперь используем 'name_with_position' вместо 'full_name_nominative'
            'name_field': 'name_with_position',
            'organization_field': 'organization',
            'subdivision_field': 'subdivision',
            'department_field': 'department'
        },
        'display_rules': {
            'hide_empty_branches': False,
            'hide_no_subdivision_no_department': False
        }
    }

    # Обычные настройки админки
    list_display = [
        'full_name_nominative',
        'organization',
        'subdivision',
        'department',
        'position',
        'is_contractor'
    ]
    list_filter = [
        'organization',
        'subdivision',
        'department',
        'position',
        'is_contractor'
    ]
    search_fields = [
        'full_name_nominative',
        'full_name_dative',
        'position__position_name'
    ]

    def get_queryset(self, request):
        """
        🔒 Ограничиваем сотрудников по организациям, доступным пользователю (если не суперпользователь).
        """
        qs = super().get_queryset(request)
        if not request.user.is_superuser and hasattr(request.user, 'profile'):
            allowed_orgs = request.user.profile.organizations.all()
            qs = qs.filter(organization__in=allowed_orgs)
        return qs

    def get_form(self, request, obj=None, **kwargs):
        """
        Переопределяем get_form, чтобы передать request.user в форму (если форма это использует).
        """
        Form = super().get_form(request, obj, **kwargs)

        class FormWithUser(Form):
            def __init__(self2, *args, **inner_kwargs):
                inner_kwargs['user'] = request.user
                super().__init__(*args, **inner_kwargs)

        return FormWithUser
