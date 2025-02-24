"""
⚙️ Admin для оборудования
"""
from django.contrib import admin
from directory.admin.mixins.tree_view import TreeViewMixin
from directory.models import Equipment
from directory.forms.equipment import EquipmentForm

@admin.register(Equipment)
class EquipmentAdmin(TreeViewMixin, admin.ModelAdmin):
    """
    ⚙️ Организация -> Подразделение -> Отдел -> Оборудование
    """
    form = EquipmentForm

    change_list_template = "admin/directory/equipment/change_list_tree.html"

    tree_settings = {
        'icons': {
            'organization': '🏢',
            'subdivision': '🏭',
            'department': '📂',
            'equipment': '⚙️',
            'no_subdivision': '🏗️',
            'no_department': '📁'
        },
        'fields': {
            'name_field': 'equipment_name',
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
        'equipment_name',
        'inventory_number',
        'organization',
        'subdivision',
        'department'
    ]
    list_filter = ['organization', 'subdivision', 'department']
    search_fields = ['equipment_name', 'inventory_number']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser and hasattr(request.user, 'profile'):
            allowed_orgs = request.user.profile.organizations.all()
            qs = qs.filter(organization__in=allowed_orgs)
        return qs
