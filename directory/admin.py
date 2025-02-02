from django.contrib import admin
from smart_selects.widgets import ChainedSelect
from .models import (
    Organization,
    StructuralSubdivision,
    Department,
    Document,
    Equipment,
    Position,
    Employee,
)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['full_name_ru', 'short_name_by']
    search_fields = ['full_name_ru', 'short_name_by']


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
    # Поле organization – обычное автодополнение, а subdivision реализовано через ChainedForeignKey в модели Department,
    # поэтому здесь оставляем autocomplete_fields только для организации.
    autocomplete_fields = ['organization']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'subdivision', 'department']
    list_filter = ['organization', 'subdivision', 'department']
    search_fields = ['name']
    # Оставляем автодополнение только для организации – для subdivision и department зададим динамические виджеты.
    autocomplete_fields = ['organization']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == 'subdivision':
            field.widget = ChainedSelect(
                to_app_name="directory",
                to_model_name="structuralsubdivision",
                chained_field="organization",
                chained_model_field="organization",
                foreign_key_app_name="directory",
                foreign_key_model_name="organization",
                foreign_key_field_name="id",
                show_all=False,
                auto_choose=True,
                sort=True
            )
        elif db_field.name == 'department':
            field.widget = ChainedSelect(
                to_app_name="directory",
                to_model_name="department",
                chained_field="subdivision",
                chained_model_field="subdivision",
                foreign_key_app_name="directory",
                foreign_key_model_name="structuralsubdivision",
                foreign_key_field_name="id",
                show_all=False,
                auto_choose=True,
                sort=True
            )
        return field


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ['equipment_name', 'inventory_number', 'organization', 'subdivision', 'department']
    list_filter = ['organization', 'subdivision', 'department']
    search_fields = ['equipment_name', 'inventory_number']
    autocomplete_fields = ['organization']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == 'subdivision':
            field.widget = ChainedSelect(
                to_app_name="directory",
                to_model_name="structuralsubdivision",
                chained_field="organization",
                chained_model_field="organization",
                foreign_key_app_name="directory",
                foreign_key_model_name="organization",
                foreign_key_field_name="id",
                show_all=False,
                auto_choose=True,
                sort=True
            )
        elif db_field.name == 'department':
            field.widget = ChainedSelect(
                to_app_name="directory",
                to_model_name="department",
                chained_field="subdivision",
                chained_model_field="subdivision",
                foreign_key_app_name="directory",
                foreign_key_model_name="structuralsubdivision",
                foreign_key_field_name="id",
                show_all=False,
                auto_choose=True,
                sort=True
            )
        return field


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ['position_name', 'organization', 'subdivision', 'department']
    list_filter = ['organization', 'subdivision', 'department', 'is_responsible_for_safety', 'is_electrical_personnel']
    search_fields = ['position_name']
    # Предполагается, что в модели Position поля subdivision и department уже реализованы через ChainedForeignKey,
    # поэтому оставляем autocomplete_fields только для организации.
    autocomplete_fields = ['organization']
    filter_horizontal = ['documents', 'equipment']


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['full_name_nominative', 'organization', 'subdivision', 'department', 'position', 'is_contractor']
    list_filter = ['organization', 'subdivision', 'department', 'position', 'is_contractor']
    search_fields = ['full_name_nominative', 'full_name_dative', 'position__position_name']
    # Оставляем автодополнение для организации, а для остальных зависимых полей заменяем виджеты
    autocomplete_fields = ['organization']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == 'subdivision':
            field.widget = ChainedSelect(
                to_app_name="directory",
                to_model_name="structuralsubdivision",
                chained_field="organization",
                chained_model_field="organization",
                foreign_key_app_name="directory",
                foreign_key_model_name="organization",
                foreign_key_field_name="id",
                show_all=False,
                auto_choose=True,
                sort=True
            )
        elif db_field.name == 'department':
            field.widget = ChainedSelect(
                to_app_name="directory",
                to_model_name="department",
                chained_field="subdivision",
                chained_model_field="subdivision",
                foreign_key_app_name="directory",
                foreign_key_model_name="structuralsubdivision",
                foreign_key_field_name="id",
                show_all=False,
                auto_choose=True,
                sort=True
            )
        elif db_field.name == 'position':
            field.widget = ChainedSelect(
                to_app_name="directory",
                to_model_name="position",
                chained_field="department",
                chained_model_field="department",
                foreign_key_app_name="directory",
                foreign_key_model_name="department",
                foreign_key_field_name="id",
                show_all=False,
                auto_choose=True,
                sort=True
            )
        return field
