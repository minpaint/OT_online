from django.contrib import admin
from directory.models.equipment import Equipment
from dal import autocomplete
from django import forms

class EquipmentForm(forms.ModelForm):
    """
    ⚙️ Форма для модели Equipment с автодополнением полей
    """
    class Meta:
        model = Equipment
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
                attrs={
                    'data-placeholder': '📂 Выберите отдел...',
                    'data-minimum-input-length': 0
                }
            ),
        }

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    """
    ⚙️ Админ-класс для модели Equipment.
    Отображает оборудование с фильтрацией по организации, подразделению и отделу.
    """
    form = EquipmentForm
    list_display = [
        'equipment_name',
        'inventory_number',
        'organization',
        'subdivision',
        'department'
    ]
    list_filter = ['organization', 'subdivision', 'department']
    search_fields = ['equipment_name', 'inventory_number']
    fieldsets = (
        ('Основная информация', {
            'fields': (
                'equipment_name',
                'inventory_number',
            )
        }),
        ('Расположение', {
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