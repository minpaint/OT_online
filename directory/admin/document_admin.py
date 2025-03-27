"""
📝 Административный интерфейс для моделей документов

Этот модуль содержит классы для регистрации моделей документов
в административном интерфейсе Django.
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from directory.models.document_template import DocumentTemplate, GeneratedDocument


@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для шаблонов документов
    """
    list_display = ('name', 'document_type', 'is_active', 'created_at', 'updated_at')
    list_filter = ('document_type', 'is_active')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'document_type', 'is_active')
        }),
        (_('Шаблон'), {
            'fields': ('template_file',)
        }),
        (_('Информация'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(GeneratedDocument)
class GeneratedDocumentAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для сгенерированных документов
    """
    list_display = ('employee', 'get_document_type', 'created_at', 'created_by')
    list_filter = ('template__document_type', 'created_at')
    search_fields = ('employee__full_name_nominative', 'template__name')
    readonly_fields = ('employee', 'template', 'document_file', 'created_at', 'created_by', 'document_data')

    def get_document_type(self, obj):
        """
        Возвращает тип документа для отображения в списке
        """
        if obj.template:
            return obj.template.get_document_type_display()
        return _('Неизвестный тип')

    get_document_type.short_description = _('Тип документа')

    def has_add_permission(self, request):
        """
        Запрещает добавление документов через админку
        """
        return False