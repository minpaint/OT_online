# admin/equipment.py
from django.contrib import admin
from smart_selects.widgets import ChainedSelect
from directory.models.equipment import Equipment

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = [
        'equipment_name',
        'inventory_number',
        'organization',
        'subdivision',
        'department'
    ]
    list_filter = [
        'organization',
        'subdivision',
        'department'
    ]
    search_fields = [
        'equipment_name',
        'inventory_number'
    ]
    autocomplete_fields = ['organization']

    fieldsets = (
        (None, {
            'fields': (
                'equipment_name',
                'inventory_number',
            )
        }),
        ('Расположение', {
            'fields': (
                'organization',
                'subdivision',
                'department',
            )
        }),
    )

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

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'organization',
            'subdivision',
            'department'
        )