# directory/admin/employee.py
from django.contrib import admin
from directory.models import Employee
from directory.models.commission import CommissionMember
from directory.forms.employee import EmployeeForm
from directory.admin.mixins.tree_view import TreeViewMixin


@admin.register(Employee)
class EmployeeAdmin(TreeViewMixin, admin.ModelAdmin):
    """
    👤 Админ-класс для модели Employee с оптимизированным отображением.
    Показывает только ключевые атрибуты: Ответственный по ОТ, Руководитель 
    стажировки, Роль в комиссии, Статус.
    """
    form = EmployeeForm

    change_list_template = "admin/directory/employee/change_list_tree.html"

    tree_settings = {
        'icons': {
            'organization': '🏢',
            'subdivision': '🏭',
            'department': '📂',
            'employee': '👤',
            'no_subdivision': '🏗️',
            'no_department': '📁'
        },
        'fields': {
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

    list_display = [
        'full_name_nominative',
        'organization',
        'subdivision',
        'department',
        'position',
        'contract_type',
        'status',
    ]
    list_filter = [
        'organization',
        'subdivision',
        'department',
        'position',
        'contract_type',
        'status',
    ]
    search_fields = [
        'full_name_nominative',
        'full_name_dative',
        'position__position_name'
    ]

    fields = [
        'full_name_nominative',
        'full_name_dative',
        'date_of_birth',
        'place_of_residence',
        'organization',
        'subdivision',
        'department',
        'position',
        'contract_type',
        'status',
        'hire_date',
        'start_date',
        'height',
        'clothing_size',
        'shoe_size',
        'is_contractor',
    ]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser and hasattr(request.user, 'profile'):
            allowed_orgs = request.user.profile.organizations.all()
            qs = qs.filter(organization__in=allowed_orgs)
        return qs.select_related(
            'organization',
            'subdivision',
            'department',
            'position'
        ).prefetch_related(
            'commission_roles',
            'commission_roles__commission'
        )

    def get_form(self, request, obj=None, **kwargs):
        Form = super().get_form(request, obj, **kwargs)

        class FormWithUser(Form):
            def __init__(self2, *args, **inner_kwargs):
                inner_kwargs['user'] = request.user
                super().__init__(*args, **inner_kwargs)

        return FormWithUser

    def get_node_additional_data(self, obj):
        """
        Получает дополнительные данные для отображения в дереве.
        Сокращенная версия с фокусом на ключевых атрибутах.
        """
        # Базовые данные о статусе
        additional_data = {
            'status': obj.status,
            'status_display': obj.get_status_display(),
            'status_emoji': self._get_status_emoji(obj.status),
        }

        # Атрибуты из позиции (должности)
        if obj.position:
            additional_data['is_responsible_for_safety'] = getattr(obj.position, 'is_responsible_for_safety', False)
            additional_data['can_be_internship_leader'] = getattr(obj.position, 'can_be_internship_leader', False)

        # Роли в комиссиях
        commission_roles = CommissionMember.objects.filter(
            employee=obj,
            is_active=True
        ).select_related('commission')

        # Для отображения в табличном виде сгруппируем роли
        additional_data['commission_roles'] = []
        for role in commission_roles:
            additional_data['commission_roles'].append({
                'commission_name': role.commission.name,
                'role': role.role,
                'role_display': role.get_role_display(),
                'role_emoji': self._get_commission_role_emoji(role.role)
            })

        return additional_data

    def _get_status_emoji(self, status):
        """Возвращает эмодзи для статуса сотрудника"""
        status_emojis = {
            'candidate': '📝',
            'active': '✅',
            'maternity_leave': '👶',
            'part_time': '⌛',
            'fired': '🚫',
        }
        return status_emojis.get(status, '❓')

    def _get_commission_role_emoji(self, role):
        """Возвращает эмодзи для роли в комиссии"""
        role_emojis = {
            'chairman': '🗳️',
            'secretary': '📝',
            'member': '👥'
        }
        return role_emojis.get(role, '❓')