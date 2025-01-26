from django.contrib import admin
from .models import (
    Organization,
    StructuralSubdivision,
    Department,
    Document,
    Equipment,
    Position,
    Employee
)

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['full_name_ru', 'short_name_by']
    search_fields = ['full_name_ru', 'full_name_by']

@admin.register(StructuralSubdivision)
class StructuralSubdivisionAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization']  # Убрал parent_subdivision
    list_filter = ['organization']
    search_fields = ['name']
    autocomplete_fields = ['organization']  # Убрал parent_subdivision

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'subdivision']
    list_filter = ['organization', 'subdivision']
    search_fields = ['name']
    autocomplete_fields = ['organization', 'subdivision']

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ['equipment_name', 'inventory_number', 'organization', 'subdivision']
    list_filter = ['organization', 'subdivision']
    search_fields = ['equipment_name', 'inventory_number']
    autocomplete_fields = ['organization', 'subdivision']

@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ['position_name', 'organization', 'subdivision', 'department']
    list_filter = ['organization', 'subdivision', 'department']
    search_fields = ['position_name']
    autocomplete_fields = ['organization', 'subdivision', 'department']
    filter_horizontal = ['documents', 'equipment']

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['full_name_nominative', 'position']  # Убрал structural_subdivision
    list_filter = ['position']  # Убрал structural_subdivision
    search_fields = ['full_name_nominative', 'full_name_dative']
    autocomplete_fields = ['position']  # Убрал structural_subdivision