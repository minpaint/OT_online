"""
👔 Админ-класс для модели Position с древовидным отображением.
Используем кастомный шаблон для вывода change list в виде таблицы.
Логика ограничения по организациям (если не суперпользователь) сохраняется.
"""

from django.contrib import admin
from directory.models import Position
from directory.forms.position import PositionForm
from directory.admin.mixins.tree_view import TreeViewMixin


@admin.register(Position)
class PositionAdmin(TreeViewMixin, admin.ModelAdmin):  # Изменен порядок наследования
    form = PositionForm

    # Указываем путь к шаблону для древовидного отображения
    change_list_template = "admin/directory/position/change_list_tree.html"  # Исправлен путь к шаблону

    # Фильтры для боковой панели
    list_filter = ['organization', 'subdivision', 'department']

    # Очищаем стандартное отображение столбцов
    list_display = []

    search_fields = [
        'position_name',
        'safety_instructions_numbers'
    ]

    # Редактирование many-to-many
    filter_horizontal = ['documents', 'equipment']

    # Настройки дерева
    tree_settings = {
        'icons': {
            'organization': '🏢',
            'subdivision': '🏭',
            'department': '📂',
            'position': '👔',
            'employee': '👤',
            'no_subdivision': '🏗️',
            'no_department': '📁'
        },
        'fields': {
            'name_field': 'position_name',
            'organization_field': 'organization',
            'subdivision_field': 'subdivision',
            'department_field': 'department'
        },
        'display_rules': {
            'hide_empty_branches': False,
            'hide_no_subdivision_no_department': False
        }
    }

    def get_queryset(self, request):
        """
        🔒 Ограничиваем должности по организациям, доступным пользователю.
        """
        qs = super().get_queryset(request).select_related(
            'organization',
            'subdivision',
            'department'
        )
        if not request.user.is_superuser and hasattr(request.user, 'profile'):
            allowed_orgs = request.user.profile.organizations.all()
            qs = qs.filter(organization__in=allowed_orgs)
        return qs

    def get_additional_node_data(self, obj):
        """
        ➕ Дополнительные данные для узла: роли и атрибуты должности.
        """
        return {
            'is_responsible_for_safety': obj.is_responsible_for_safety,
            'can_be_internship_leader': obj.can_be_internship_leader,
            'commission_role': obj.commission_role,
            'is_electrical_personnel': obj.is_electrical_personnel,
        }

    def has_module_permission(self, request):
        """
        👮‍♂️ Проверка прав на доступ к модулю
        """
        if request.user.is_superuser:
            return True
        if hasattr(request.user, 'profile'):
            return request.user.profile.organizations.exists()
        return False

    def has_view_permission(self, request, obj=None):
        """
        👀 Проверка прав на просмотр
        """
        if request.user.is_superuser:
            return True
        if not obj:
            return True
        if hasattr(request.user, 'profile'):
            return obj.organization in request.user.profile.organizations.all()
        return False

    def has_change_permission(self, request, obj=None):
        """
        ✏️ Проверка прав на редактирование
        """
        return self.has_view_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        """
        🗑️ Проверка прав на удаление
        """
        return self.has_view_permission(request, obj)

    def has_add_permission(self, request):
        """
        ➕ Проверка прав на добавление
        """
        if request.user.is_superuser:
            return True
        if hasattr(request.user, 'profile'):
            return request.user.profile.organizations.exists()
        return False