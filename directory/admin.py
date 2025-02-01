# directory/admin.py

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
    list_display = ['name', 'organization']
    list_filter = ['organization']
    search_fields = ['name']
    autocomplete_fields = ['organization']


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'subdivision']
    list_filter = ['organization', 'subdivision']
    search_fields = ['name']
    autocomplete_fields = ['organization', 'subdivision']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'subdivision', 'department']
    list_filter = ['organization', 'subdivision', 'department']
    search_fields = ['name']
    autocomplete_fields = ['organization', 'subdivision', 'department']


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = [
        'equipment_name',
        'inventory_number',
        'organization',
        'subdivision',
        'department'
    ]
    list_filter = ['organization', 'subdivision', 'department']
    search_fields = ['equipment_name', 'inventory_number']
    autocomplete_fields = ['organization', 'subdivision', 'department']


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = [
        'position_name',
        'organization',
        'subdivision',
        'department'
    ]
    list_filter = [
        'organization',
        'subdivision',
        'department',
        'is_responsible_for_safety',
        'is_electrical_personnel'
    ]
    search_fields = ['position_name']
    autocomplete_fields = ['organization', 'subdivision', 'department']
    filter_horizontal = ['documents', 'equipment']

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj is None:
            return form

        # Фильтрация подразделений по организации
        if 'organization' in form.base_fields and 'subdivision' in form.base_fields:
            organization_id = obj.organization_id if obj else None
            if organization_id:
                form.base_fields['subdivision'].queryset = (
                    form.base_fields['subdivision'].queryset
                    .filter(organization_id=organization_id)
                )

        # Фильтрация отделов по подразделению
        if 'subdivision' in form.base_fields and 'department' in form.base_fields:
            subdivision_id = obj.subdivision_id if obj else None
            if subdivision_id:
                form.base_fields['department'].queryset = (
                    form.base_fields['department'].queryset
                    .filter(subdivision_id=subdivision_id)
                )

        return form

    class Media:
        js = ('directory/js/admin_dependent_dropdowns.js',)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
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
    autocomplete_fields = [
        'organization',
        'subdivision',
        'department',
        'position'
    ]
    fieldsets = (
        ('Основная информация', {
            'fields': (
                'full_name_nominative',
                'full_name_dative',
                'date_of_birth',
                'place_of_residence'
            )
        }),
        ('Место работы', {
            'fields': (
                'organization',
                'subdivision',
                'department',
                'position'
            )
        }),
        ('Дополнительная информация', {
            'fields': (
                'is_contractor',
                'height',
                'clothing_size',
                'shoe_size'
            )
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj is None:
            return form

        # Фильтруем подразделения по организации
        if 'organization' in form.base_fields and 'subdivision' in form.base_fields:
            organization_id = obj.organization_id if obj else None
            if organization_id:
                form.base_fields['subdivision'].queryset = (
                    form.base_fields['subdivision'].queryset
                    .filter(organization_id=organization_id)
                )

        # Фильтруем отделы по подразделению
        if 'subdivision' in form.base_fields and 'department' in form.base_fields:
            subdivision_id = obj.subdivision_id if obj else None
            if subdivision_id:
                form.base_fields['department'].queryset = (
                    form.base_fields['department'].queryset
                    .filter(subdivision_id=subdivision_id)
                )

        # Фильтруем должности
        if all(field in form.base_fields for field in ['organization', 'subdivision', 'department']):
            position_queryset = form.base_fields['position'].queryset

            if obj.organization_id:
                position_queryset = position_queryset.filter(
                    organization_id=obj.organization_id
                )
            if obj.subdivision_id:
                position_queryset = position_queryset.filter(
                    subdivision_id=obj.subdivision_id
                )
            if obj.department_id:
                position_queryset = position_queryset.filter(
                    department_id=obj.department_id
                )

            form.base_fields['position'].queryset = position_queryset

        return form

    class Media:
        js = ('directory/js/admin_dependent_dropdowns.js',)