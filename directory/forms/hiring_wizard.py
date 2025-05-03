# directory/forms/hiring_wizard.py
from django import forms
from dal import autocomplete
from directory.models import Employee, EmployeeHiring
from directory.models.medical_examination import HarmfulFactor
from directory.models.medical_norm import MedicalExaminationNorm


class Step1BasicInfoForm(forms.Form):
    """Базовые данные о сотруднике и должности"""
    organization = forms.ModelChoiceField(
        queryset=None,  # Будет заполнено в __init__
        label="Организация",
        required=True,
        widget=autocomplete.ModelSelect2(
            url='directory:organization-autocomplete',
            attrs={
                'data-placeholder': '🏢 Выберите организацию...',
                'class': 'select2-basic form-control'
            }
        )
    )

    subdivision = forms.ModelChoiceField(
        queryset=None,
        label="Структурное подразделение",
        required=False,
        widget=autocomplete.ModelSelect2(
            url='directory:subdivision-autocomplete',
            forward=['organization'],
            attrs={
                'data-placeholder': '🏭 Выберите подразделение...',
                'class': 'select2-basic form-control'
            }
        )
    )

    department = forms.ModelChoiceField(
        queryset=None,
        label="Отдел",
        required=False,
        widget=autocomplete.ModelSelect2(
            url='directory:department-autocomplete',
            forward=['subdivision'],
            attrs={
                'data-placeholder': '📂 Выберите отдел...',
                'class': 'select2-basic form-control'
            }
        )
    )

    position = forms.ModelChoiceField(
        queryset=None,
        label="Должность",
        required=True,
        widget=autocomplete.ModelSelect2(
            url='directory:position-autocomplete',
            forward=['organization', 'subdivision', 'department'],
            attrs={
                'data-placeholder': '👔 Выберите должность...',
                'class': 'select2-basic form-control'
            }
        )
    )

    full_name_nominative = forms.CharField(
        label="ФИО (именительный падеж)",
        max_length=255,
        required=True
    )

    # Дополнительно: тип приема
    hiring_type = forms.ChoiceField(
        label="Вид приема",
        choices=EmployeeHiring.HIRING_TYPE_CHOICES,
        initial='new',
        required=True
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Ограничиваем организации по профилю пользователя
        if self.user and hasattr(self.user, 'profile'):
            user_orgs = self.user.profile.organizations.all()
            self.fields['organization'].queryset = user_orgs

            # Подставляем организацию автоматически, если она одна
            if user_orgs.count() == 1:
                org = user_orgs.first()
                self.initial['organization'] = org.id


class Step2MedicalInfoForm(forms.Form):
    """Информация для медосмотра"""
    date_of_birth = forms.DateField(
        label="Дата рождения",
        required=True,
        widget=forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')
    )

    place_of_residence = forms.CharField(
        label="Место проживания",
        required=True,
        widget=forms.Textarea(attrs={'rows': 3})
    )


class Step3SIZInfoForm(forms.Form):
    """Информация для СИЗ"""
    height = forms.ChoiceField(
        label="Рост",
        choices=Employee.HEIGHT_CHOICES,
        required=False
    )

    clothing_size = forms.ChoiceField(
        label="Размер одежды",
        choices=Employee.CLOTHING_SIZE_CHOICES,
        required=False
    )

    shoe_size = forms.ChoiceField(
        label="Размер обуви",
        choices=Employee.SHOE_SIZE_CHOICES,
        required=False
    )