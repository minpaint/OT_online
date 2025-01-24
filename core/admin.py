from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import (
    Organization,
    Position,
    Employee,
    Document,
    OrganizationalUnit
)
from .resources import (
    OrganizationResource,
    PositionResource,
    EmployeeResource
)
from mptt.admin import MPTTModelAdmin

@admin.register(OrganizationalUnit)
class OrganizationalUnitAdmin(MPTTModelAdmin):
    list_display = ['name', 'code', 'unit_type', 'parent']
    list_filter = ['unit_type']
    search_fields = ['name', 'code']
    mptt_level_indent = 20

@admin.register(Organization)
class OrganizationAdmin(ImportExportModelAdmin):
    resource_class = OrganizationResource
    list_display = ['short_name_ru', 'name_ru', 'inn', 'created_at', 'updated_at']
    search_fields = ['short_name_ru', 'name_ru', 'inn']
    list_filter = ['created_at', 'updated_at']

@admin.register(Position)
class PositionAdmin(ImportExportModelAdmin):
    resource_class = PositionResource
    list_display = [
        'name',
        'organizational_unit',
        'is_electrical_personnel',
        'electrical_safety_group',
        'is_internship_supervisor',
        'internship_period'
    ]
    list_filter = [
        'organizational_unit',
        'is_electrical_personnel',
        'is_internship_supervisor'
    ]
    search_fields = ['name']
    filter_horizontal = ['documents']

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('documents')

@admin.register(Employee)
class EmployeeAdmin(ImportExportModelAdmin):
    resource_class = EmployeeResource
    list_display = [
        'full_name',
        'position',
        'birth_date',
        'phone',
        'email'
    ]
    list_filter = ['position__organizational_unit']
    search_fields = ['full_name', 'phone', 'email']

@admin.register(Document)
class DocumentAdmin(ImportExportModelAdmin):
    list_display = [
        'name',
        'created_at',
        'updated_at'
    ]
    list_filter = [
        'created_at',
        'updated_at'
    ]
    search_fields = ['name']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    class Media:
        js = ('admin/js/dependent_dropdowns.js',)