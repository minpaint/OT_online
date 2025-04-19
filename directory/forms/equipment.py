# directory/forms/equipment.py
from django import forms
from django.utils import timezone
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Fieldset, Div, HTML
from dal import autocomplete
from directory.models import Equipment
from directory.forms.mixins import OrganizationRestrictionFormMixin


class EquipmentForm(OrganizationRestrictionFormMixin, forms.ModelForm):
    """
    ⚙️ Форма для оборудования с ограничением по организациям

    Использует автодополнение для выбора организации, подразделения и отдела,
    и фильтрует данные согласно разрешённым организациям из профиля пользователя.
    Добавлены поля для технического обслуживания.
    """

    class Meta:
        model = Equipment
        fields = [
            'equipment_name', 'inventory_number',
            'organization', 'subdivision', 'department',
            'maintenance_period_days', 'last_maintenance_date',
            'next_maintenance_date', 'maintenance_status'
        ]
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
            'last_maintenance_date': forms.DateInput(
                attrs={'type': 'date'},
                format='%Y-%m-%d'
            ),
            'next_maintenance_date': forms.DateInput(
                attrs={'type': 'date'},
                format='%Y-%m-%d'
            ),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # 🎨 Настройка crispy-forms
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Fieldset(
                'Основная информация',
                'equipment_name',
                'inventory_number',
                'organization',
                'subdivision',
                'department',
            ),
            Fieldset(
                'Техническое обслуживание',
                'maintenance_period_days',
                'last_maintenance_date',
                'next_maintenance_date',
                'maintenance_status',
            ),
            HTML('<hr>'),
            Div(
                Submit('submit', '💾 Сохранить', css_class='btn-primary'),
                HTML('<a href="{% url "directory:equipment:equipment_list" %}" class="btn btn-secondary">Отмена</a>'),
                css_class='d-flex justify-content-between mt-3'
            )
        )

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

    def clean(self):
        cleaned_data = super().clean()

        # Если указана дата последнего ТО, но не указана дата следующего -
        # рассчитываем её автоматически
        last_maintenance = cleaned_data.get('last_maintenance_date')
        next_maintenance = cleaned_data.get('next_maintenance_date')
        maintenance_period = cleaned_data.get('maintenance_period_days')

        if last_maintenance and not next_maintenance and maintenance_period:
            from datetime import timedelta
            cleaned_data['next_maintenance_date'] = last_maintenance + timedelta(days=maintenance_period)

        return cleaned_data