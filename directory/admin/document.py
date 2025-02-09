from django.contrib import admin
from directory.models.document import Document
from dal import autocomplete
from django import forms

class DocumentForm(forms.ModelForm):
    """
    📄 Форма для модели Document с автодополнением полей
    """
    class Meta:
        model = Document
        fields = '__all__'
        widgets = {
            'organization': autocomplete.ModelSelect2(
                url='directory:organization-autocomplete',
                attrs={'data-placeholder': '🏢 Выберите организацию...'}
            ),
            'subdivision': autocomplete.ModelSelect2(
                url='directory:subdivision-autocomplete',
                forward=['organization'],
                attrs={'data-placeholder': '🏭 Выберите подразделение...'}
            ),
            'department': autocomplete.ModelSelect2(
                url='directory:department-autocomplete',
                forward=['subdivision'],
                attrs={'data-placeholder': '📂 Выберите отдел...'}
            ),
        }

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """
    📄 Админ-класс для модели Document.
    Отображает документы с фильтрацией по организации, подразделению и отделу.
    """
    form = DocumentForm
    list_display = ['name', 'organization', 'subdivision', 'department']
    list_filter = ['organization', 'subdivision', 'department']
    search_fields = ['name']
    fieldsets = (
        (None, {
            'fields': ('name',)
        }),
        ('Принадлежность', {
            'fields': (
                'organization',
                'subdivision',
                'department'
            )
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'organization',
            'subdivision',
            'department'
        )