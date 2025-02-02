from django.contrib import admin
from directory.models.document import Document

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'subdivision', 'department']
    list_filter = ['organization', 'subdivision', 'department']
    search_fields = ['name']
    autocomplete_fields = ['organization']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'organization', 'subdivision', 'department'
        )