from django.contrib import admin
from directory.models.organization import Organization

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = [
        'full_name_ru',
        'short_name_ru',
        'full_name_by',
        'short_name_by',
    ]
    search_fields = [
        'full_name_ru',
        'short_name_ru',
        'full_name_by',
        'short_name_by',
    ]