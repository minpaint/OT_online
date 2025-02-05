# admin/subdivision.py
from django.contrib import admin
from directory.models.subdivision import StructuralSubdivision


@admin.register(StructuralSubdivision)
class StructuralSubdivisionAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'short_name',
        'organization'
    ]
    list_filter = ['organization']
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
                'organization'
            )
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization')