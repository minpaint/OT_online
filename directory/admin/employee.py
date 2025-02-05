# admin/employee.py
from django.contrib import admin
from smart_selects.widgets import ChainedSelect
from directory.models.employee import Employee

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
        'is_contractor',
        'clothing_size',
        'shoe_size'
    ]
    search_fields = [
        'full_name_nominative',
        'full_name_dative',
        'position__position_name'
    ]
    autocomplete_fields = ['organization']

    fieldsets = (
        ('Персональные данные', {
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
                'is_contractor',
            )
        }),
        ('Спецодежда', {
            'fields': (
                'height',
                'clothing_size',
                'shoe_size',
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
        elif db_field.name == 'position':
            field.widget = ChainedSelect(
                to_app_name="directory",
                to_model_name="position",
                chained_field="organization",  # Изменено с department на organization
                chained_model_field="organization",
                foreign_key_app_name="directory",
                foreign_key_model_name="organization",
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
            'department',
            'position'
        )