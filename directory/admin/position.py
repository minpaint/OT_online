# admin/position.py
from django.contrib import admin
from smart_selects.widgets import ChainedSelect
from directory.models.position import Position

@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = [
        'position_name', 
        'organization', 
        'subdivision', 
        'department',
        'electrical_safety_group',
        'is_responsible_for_safety',
        'is_electrical_personnel'
    ]
    list_filter = [
        'organization', 
        'subdivision', 
        'department', 
        'electrical_safety_group',
        'is_responsible_for_safety',
        'is_electrical_personnel'
    ]
    search_fields = ['position_name', 'safety_instructions_numbers']
    filter_horizontal = ['documents', 'equipment']
    autocomplete_fields = ['organization']

    fieldsets = (
        (None, {
            'fields': ('position_name',)
        }),
        ('Принадлежность', {
            'fields': (
                'organization',
                'subdivision',
                'department',
            )
        }),
        ('Безопасность', {
            'fields': (
                'safety_instructions_numbers',
                'electrical_safety_group',
                'internship_period_days',
                'is_responsible_for_safety',
                'is_electrical_personnel',
            )
        }),
        ('Связанные документы и оборудование', {
            'fields': (
                'documents',
                'equipment',
            ),
            'classes': ('collapse',)
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
        ).prefetch_related('documents', 'equipment')