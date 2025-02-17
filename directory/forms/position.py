# directory/forms/position.py
"""
👔 Форма для должностей с ограничением по организациям

Использует автодополнение для выбора организации, подразделения, отдела,
а также документов и оборудования, связанных с должностью.
Данные фильтруются по разрешённым организациям из профиля пользователя. 🚀
"""

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from dal import autocomplete
from directory.models import Position
from .mixins import OrganizationRestrictionFormMixin  # Импорт миксина 🚀


class PositionForm(OrganizationRestrictionFormMixin, forms.ModelForm):
    class Meta:
        model = Position
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
            'documents': autocomplete.ModelSelect2Multiple(
                url='directory:document-autocomplete',
                forward=['organization', 'subdivision', 'department'],
                attrs={'data-placeholder': '📄 Выберите документы...'}
            ),
            'equipment': autocomplete.ModelSelect2Multiple(
                url='directory:equipment-autocomplete',
                forward=['organization', 'subdivision', 'department'],
                attrs={'data-placeholder': '⚙️ Выберите оборудование...'}
            )
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # 🎨 Настройка crispy-forms
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', '💾 Сохранить'))

        # Ограничиваем поле организации по профилю пользователя 🔒
        if self.user and hasattr(self.user, 'profile'):
            user_orgs = self.user.profile.organizations.all()
            self.fields['organization'].queryset = user_orgs
