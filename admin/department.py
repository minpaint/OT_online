from django.contrib import admin
from directory.models.department import Department

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'short_name', 'organization', 'subdivision']
    list_filter = ['organization', 'subdivision']
    search_fields = ['name', 'short_name']
    autocomplete_fields = ['organization']