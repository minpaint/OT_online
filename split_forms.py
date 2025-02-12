import os
import shutil
from pathlib import Path

# Структура форм
FORMS = {
    'organization.py': '''from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from directory.models import Organization

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
''',

    'subdivision.py': '''from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from dal import autocomplete
from directory.models import StructuralSubdivision

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
''',

    'department.py': '''from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from dal import autocomplete
from directory.models import Department

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
''',

    'position.py': '''from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from dal import autocomplete
from directory.models import Position

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
''',

    'employee.py': '''from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from dal import autocomplete
from directory.models import Employee

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
''',

    'employee_hiring.py': '''from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, HTML
from dal import autocomplete
from directory.models import Employee

class EmployeeHiringForm(forms.ModelForm):
    """📝 Форма приема на работу"""
    preview = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.HiddenInput()
    )

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
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('full_name_nominative', css_class='form-group col-md-6'),
                Column('full_name_dative', css_class='form-group col-md-6'),
                css_class='form-row'
            ),
            Row(
                Column('date_of_birth', css_class='form-group col-md-6'),
                Column('place_of_residence', css_class='form-group col-md-6'),
                css_class='form-row'
            ),
            Row(
                Column('organization', css_class='form-group col-md-6'),
                Column('subdivision', css_class='form-group col-md-6'),
                css_class='form-row'
            ),
            Row(
                Column('department', css_class='form-group col-md-6'),
                Column('position', css_class='form-group col-md-6'),
                css_class='form-row'
            ),
            Row(
                Column('height', css_class='form-group col-md-4'),
                Column('clothing_size', css_class='form-group col-md-4'),
                Column('shoe_size', css_class='form-group col-md-4'),
                css_class='form-row'
            ),
            'is_contractor',
            HTML("<hr>"),
            Row(
                Column(
                    Submit('preview', '👁 Предпросмотр', css_class='btn-info'),
                    css_class='form-group col-6'
                ),
                Column(
                    Submit('submit', '💾 Принять на работу', css_class='btn-success'),
                    css_class='form-group col-6'
                ),
                css_class='form-row'
            )
        )

        if user:
            # Фильтруем организации по доступу пользователя
            self.fields['organization'].queryset = user.profile.organizations.all()
'''
}

# Содержимое __init__.py
INIT_CONTENT = '''from .organization import OrganizationForm
from .subdivision import StructuralSubdivisionForm
from .department import DepartmentForm
from .position import PositionForm
from .employee import EmployeeForm
from .employee_hiring import EmployeeHiringForm

__all__ = [
    'OrganizationForm',
    'StructuralSubdivisionForm',
    'DepartmentForm',
    'PositionForm',
    'EmployeeForm',
    'EmployeeHiringForm',
]
'''


def create_forms_structure():
    """Создание структуры форм"""
    # Создаем директорию forms если её нет
    forms_dir = Path('directory/forms')
    forms_dir.mkdir(parents=True, exist_ok=True)

    # Создаем файлы форм
    for filename, content in FORMS.items():
        file_path = forms_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

    # Создаем __init__.py
    init_path = forms_dir / '__init__.py'
    with open(init_path, 'w', encoding='utf-8') as f:
        f.write(INIT_CONTENT)

    # Удаляем старый forms.py если он существует
    old_forms = Path('directory/forms.py')
    if old_forms.exists():
        old_forms.unlink()


def main():
    """Основная функция"""
    try:
        create_forms_structure()
        print("✅ Формы успешно разделены!")
        print("\n📋 Структура форм:")
        print("directory/")
        print("└── forms/")
        print("    ├── __init__.py")
        for form in FORMS.keys():
            print(f"    ├── {form}")

        print("\n⚠️ Не забудьте:")
        print("1. Проверить импорты в других файлах")
        print("2. Выполнить тесты")
        print("3. Закоммитить изменения")

    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")


if __name__ == '__main__':
    main()