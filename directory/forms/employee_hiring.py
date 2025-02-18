from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from dal import autocomplete
from directory.models import Employee
from .mixins import OrganizationRestrictionFormMixin  # Импорт миксина 🚀


class EmployeeHiringForm(OrganizationRestrictionFormMixin, forms.ModelForm):
    """
    👥 Форма для найма сотрудника, использующая django-autocomplete-light (DAL).
    """

    class Meta:
        model = Employee
        fields = [
            'full_name_nominative',    # ФИО (именительный)
            'full_name_dative',        # ФИО (дательный)
            'organization',            # 🏢 Организация
            'subdivision',             # 🏭 Подразделение
            'department',              # 📂 Отдел
            'position',                # 👔 Должность
            'date_of_birth',           # 📅 Дата рождения
            'is_contractor'            # Договор подряда?
        ]
        widgets = {
            'organization': autocomplete.ModelSelect2(
                url='directory:organization-autocomplete',
                attrs={
                    'data-placeholder': '🏢 Выберите организацию...',
                    'class': 'select2 form-control',         # Класс для инициализации
                    'data-theme': 'bootstrap4'  # Указываем тему через data-атрибут
                }
            ),
            'subdivision': autocomplete.ModelSelect2(
                url='directory:subdivision-autocomplete',
                forward=['organization'],
                attrs={
                    'data-placeholder': '🏭 Выберите подразделение...',
                    'class': 'select2 form-control',
                    'data-theme': 'bootstrap4'
                }
            ),
            'department': autocomplete.ModelSelect2(
                url='directory:department-autocomplete',
                forward=['subdivision'],
                attrs={
                    'data-placeholder': '📂 Выберите отдел...',
                    'class': 'select2 form-control',
                    'data-theme': 'bootstrap4'
                }
            ),
            'position': autocomplete.ModelSelect2(
                url='directory:position-autocomplete',
                forward=['organization', 'subdivision', 'department'],
                attrs={
                    'data-placeholder': '👔 Выберите должность...',
                    'class': 'select2 form-control',
                    'data-theme': 'bootstrap4'
                }
            ),
            'date_of_birth': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'},
                format='%Y-%m-%d'
            )
        }

    def __init__(self, *args, **kwargs):
        # 🔑 Извлекаем пользователя, если передан
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # 🎨 Настройка crispy-forms
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', '💾 Принять'))

        # 🔒 Ограничиваем выбор организаций по профилю пользователя
        if self.user and hasattr(self.user, 'profile'):
            user_orgs = self.user.profile.organizations.all()
            self.fields['organization'].queryset = user_orgs
            # Если у пользователя ровно одна организация – выбираем её по умолчанию
            if user_orgs.count() == 1:
                self.initial['organization'] = user_orgs.first().id
