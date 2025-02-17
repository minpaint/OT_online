# directory/forms/equipment.py
"""
⚙️ Форма для оборудования с ограничением по организациям

Использует автодополнение для выбора организации, подразделения и отдела,
и фильтрует данные согласно разрешённым организациям из профиля пользователя. 🚀
"""

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from dal import autocomplete
from directory.models import Equipment
from .mixins import OrganizationRestrictionFormMixin  # Импорт миксина 🚀


class EquipmentForm(OrganizationRestrictionFormMixin, forms.ModelForm):
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
                attrs={'data-placeholder': '📂 Выберите отдел...'}
            ),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # 🎨 Настройка crispy-forms
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', '💾 Сохранить'))

        # Ограничиваем выбор организаций по профилю пользователя 🔒
        if self.user and hasattr(self.user, 'profile'):
            user_orgs = self.user.profile.organizations.all()
            self.fields['organization'].queryset = user_orgs
            if user_orgs.count() == 1:
                org = user_orgs.first()
                self.initial['organization'] = org.id
                self.fields['subdivision'].queryset = org.subdivisions.all()
            else:
                self.fields['subdivision'].queryset = Equipment.objects.none()

            self.fields['department'].queryset = Equipment.objects.none()
