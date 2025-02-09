from django.contrib import admin
from django.shortcuts import render
from directory.models.employee import Employee
from directory.forms import EmployeeForm


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    """
    👤 Админ-класс для модели Employee (Сотрудник).
    """
    form = EmployeeForm
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
        'is_contractor',
        'clothing_size',
        'shoe_size',
    ]
    search_fields = [
        'full_name_nominative',
        'full_name_dative',
        'position__position_name'
    ]
    fieldsets = (
        (None, {
            'fields': (
                'full_name_nominative',
                'full_name_dative',
                'date_of_birth',
                'place_of_residence',
            )
        }),
        ('Организационная структура', {
            'fields': (
                'organization',
                'subdivision',
                'department',
                'position',
            )
        }),
        ('Дополнительная информация', {
            'fields': (
                'height',
                'clothing_size',
                'shoe_size',
                'is_contractor',
            ),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'organization',
            'subdivision',
            'department',
            'position'
        )

    def changelist_view(self, request, extra_context=None):
        """
        🔄 Переопределение представления списка для группировки сотрудников в дерево.
        """
        response = super().changelist_view(request, extra_context)

        try:
            qs = response.context_data['cl'].queryset
        except (AttributeError, KeyError):
            return response

        # Группировка сотрудников по структуре
        tree = {}
        for emp in qs:
            org = emp.organization
            if org not in tree:
                tree[org] = {}
            org_group = tree[org]

            sub = emp.subdivision if emp.subdivision else "Без подразделения"
            if sub not in org_group:
                org_group[sub] = {}
            sub_group = org_group[sub]

            dept = emp.department if emp.department else "Без отдела"
            if dept not in sub_group:
                sub_group[dept] = []
            sub_group[dept].append(emp)

        response.context_data['employee_tree'] = tree
        return response