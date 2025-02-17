from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from dal import autocomplete
from directory.models import Employee

class EmployeeHiringForm(forms.ModelForm):
    """
    👥 Форма для найма сотрудника.
    Включает выбор организации, подразделения и должности с автодополнением.
    """

    class Meta:
        model = Employee
        fields = [
            'full_name_nominative', 'full_name_dative',
            'organization', 'subdivision', 'department', 'position',
            'date_of_birth', 'is_contractor'
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
            'position': autocomplete.ModelSelect2(
                url='directory:position-autocomplete',
                forward=['organization', 'subdivision', 'department'],
                attrs={'data-placeholder': '👔 Выберите должность...'}
            ),
            'date_of_birth': forms.DateInput(
                attrs={'type': 'date'},
                format='%Y-%m-%d'
            )
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # 🎨 Настройка crispy-forms
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', '💾 Сохранить'))

        # 🏢 Ограничиваем выбор организаций по профилю пользователя
        if self.user and hasattr(self.user, 'profile'):
            user_orgs = self.user.profile.organizations.all()
            self.fields['organization'].queryset = user_orgs
            if user_orgs.count() == 1:
                self.initial['organization'] = user_orgs.first().id
