from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from dal import autocomplete
from directory.models import (
    Organization,
    StructuralSubdivision,
    Department,
    Document,
    Equipment,
    Position,
    Employee
)


class OrganizationForm(forms.ModelForm):
    """🏢 Форма для организаций"""

    class Meta:
        model = Organization
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', '💾 Сохранить'))


class StructuralSubdivisionForm(forms.ModelForm):
    """🏭 Форма для структурных подразделений"""

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
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', '💾 Сохранить'))


class DepartmentForm(forms.ModelForm):
    """📂 Форма для отделов"""

    class Meta:
        model = Department
        fields = ['name', 'short_name', 'organization', 'subdivision']
        widgets = {
            'organization': autocomplete.ModelSelect2(
                url='directory:organization-autocomplete',
                attrs={'data-placeholder': '🏢 Выберите организацию...'}
            ),
            'subdivision': autocomplete.ModelSelect2(
                url='directory:subdivision-autocomplete',
                forward=['organization'],
                attrs={'data-placeholder': '🏭 Выберите подразделение...'}
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', '💾 Сохранить'))


class PositionForm(forms.ModelForm):
    """👔 Форма для должностей"""

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
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', '💾 Сохранить'))


class EmployeeForm(forms.ModelForm):
    """👤 Форма для сотрудников"""

    class Meta:
        model = Employee
        fields = [
            'full_name_nominative', 'full_name_dative',
            'date_of_birth', 'place_of_residence',
            'organization', 'subdivision', 'department', 'position',
            'height', 'clothing_size', 'shoe_size',
            'is_contractor'
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
                attrs={
                    'data-placeholder': '📂 Выберите отдел...',
                    'data-minimum-input-length': 0
                }
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
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', '💾 Сохранить'))

        # Настройка обязательных полей
        self.fields['subdivision'].required = False
        self.fields['department'].required = False