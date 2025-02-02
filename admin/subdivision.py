from django.contrib import admin
from directory.models.subdivision import StructuralSubdivision

@admin.register(StructuralSubdivision)
class StructuralSubdivisionAdmin(admin.ModelAdmin):
    list_display = ['name', 'short_name', 'organization']
    list_filter = ['organization']
    search_fields = ['name', 'short_name']
    autocomplete_fields = ['organization']