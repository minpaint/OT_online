# admin/department.py
from django.contrib import admin
from smart_selects.widgets import ChainedSelect
from directory.models.department import Department

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'short_name',
        'organization',
        'subdivision'
    ]
    list_filter = [
        'organization',
        'subdivision'
    ]
    search_fields = [
        'name',
        'short_name'
    ]
    autocomplete_fields = ['organization']

    fieldsets = (
        (None, {
            'fields': (
                'name',
                'short_name',
                'organization',
                'subdivision'
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
        return field

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'organization',
            'subdivision'
        )