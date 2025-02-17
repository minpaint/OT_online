# directory/forms/subdivision.py
"""
🏭 Форма для структурных подразделений с ограничением по организациям

Использует автодополнение для выбора организации и родительского подразделения.
Данные фильтруются по разрешённым организациям из профиля пользователя. 🚀
"""

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from dal import autocomplete
from directory.models import StructuralSubdivision
from .mixins import OrganizationRestrictionFormMixin  # Импорт миксина 🚀


class StructuralSubdivisionForm(OrganizationRestrictionFormMixin, forms.ModelForm):
    class Meta:
        model = StructuralSubdivision
        fields = ['name', 'short_name', 'organization', 'parent']
        widgets = {
            'organization': autocomplete.ModelSelect2(
                url='directory:organization-autocomplete',
                attrs={'data-placeholder': '🏢 Выберите организацию...'}
            ),
            'parent': autocomplete.ModelSelect2(
                url='directory:subdivision-autocomplete',
                forward=['organization'],
                attrs={'data-placeholder': '🏭 Выберите родительское подразделение...'}
            )
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # 🎨 Настройка crispy-forms
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', '💾 Сохранить'))
