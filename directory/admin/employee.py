from django.contrib import admin
from directory.models import Employee
from directory.models.commission import CommissionMember
from directory.forms.employee import EmployeeForm
from directory.admin.mixins.tree_view import TreeViewMixin


@admin.register(Employee)
class EmployeeAdmin(TreeViewMixin, admin.ModelAdmin):
    """
    👤 Админ-класс для модели Employee.
    Здесь используем TreeViewMixin, чтобы выводить древовидную структуру
    (Организация → Подразделение → Отдел → Сотрудник)
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
            'name_field': 'name_with_position',  # теперь рассчитано с учётом contract_type
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
        'contract_type',  # используем contract_type вместо status
    ]
    list_filter = [
        'organization',
        'subdivision',
        'department',
        'position',
        'contract_type',  # используем contract_type вместо status
    ]
    search_fields = [
        'full_name_nominative',
        'full_name_dative',
        'position__position_name'
    ]
    actions = ['mark_as_fired']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser and hasattr(request.user, 'profile'):
            allowed_orgs = request.user.profile.organizations.all()
            qs = qs.filter(organization__in=allowed_orgs)
        return qs

    def get_form(self, request, obj=None, **kwargs):
        Form = super().get_form(request, obj, **kwargs)

        class FormWithUser(Form):
            def __init__(self2, *args, **inner_kwargs):
                inner_kwargs['user'] = request.user
                super().__init__(*args, **inner_kwargs)

        return FormWithUser

    def mark_as_fired(self, request, queryset):
        updated = queryset.update(contract_type='fired')
        self.message_user(request, f"Отмечено как уволенные: {updated}")

    mark_as_fired.short_description = "Отметить как уволенных"

    def get_node_additional_data(self, obj):
        """
        Получает дополнительные данные для отображения в дереве
        """
        additional_data = {}

        # Добавляем статус сотрудника из contract_type
        additional_data['contract_type'] = obj.contract_type
        additional_data['contract_type_display'] = obj.get_contract_type_display()

        # Добавляем атрибуты из position
        if obj.position:
            additional_data['is_responsible_for_safety'] = obj.position.is_responsible_for_safety
            additional_data['can_be_internship_leader'] = obj.position.can_be_internship_leader
            additional_data['is_electrical_personnel'] = obj.position.is_electrical_personnel
            additional_data['electrical_group'] = obj.position.electrical_safety_group

        # Получаем роли в комиссиях
        commissions = CommissionMember.objects.filter(
            employee=obj,
            is_active=True
        ).select_related('commission')

        # Добавляем данные о комиссиях
        additional_data['commissions'] = []
        for member in commissions:
            additional_data['commissions'].append({
                'name': member.commission.name,
                'role': member.role,
                'role_display': member.get_role_display()
            })

        return additional_data