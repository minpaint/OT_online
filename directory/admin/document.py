# 📁 directory/admin/document.py
from django.contrib import admin  # 🛠️ Импорт админки Django
from directory.models.document import Document  # 📄 Импорт модели Document

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """
    ⚙️ Админ-класс для модели Document.
    Отображает документы с фильтрацией по организации, подразделению и отделу.
    """
    list_display = ['name', 'organization', 'subdivision', 'department']
    list_filter = ['organization', 'subdivision', 'department']
    search_fields = ['name']

    fieldsets = (
        (None, {'fields': ('name',)}),
        ('Принадлежность', {'fields': ('organization', 'subdivision', 'department')}),
    )

    def get_queryset(self, request):
        """
        ⚡️ Оптимизация запросов с помощью select_related.
        """
        return super().get_queryset(request).select_related('organization', 'subdivision', 'department')
