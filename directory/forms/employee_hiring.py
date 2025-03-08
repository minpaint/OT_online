# directory/forms/employee_hiring.py
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from dal import autocomplete

# Миксин, который ограничивает список организаций по профилю пользователя
from directory.forms.mixins import OrganizationRestrictionFormMixin

# Прямой импорт модели Employee (если нет круга).
# Если будет ошибка ImportError из-за циклического импорта, см. комментарии ниже.
from directory.models.employee import Employee

class EmployeeHiringForm(OrganizationRestrictionFormMixin, forms.ModelForm):
    """
    👥 Форма для найма сотрудника, использующая django-autocomplete-light (DAL).
    Содержит все поля модели Employee, включая место проживания, рост и т.д.
    """

    class Meta:
        model = Employee
        fields = [
            'full_name_nominative',   # ФИО (именительный) 📝
            'full_name_dative',       # ФИО (дательный) ✍️
            'date_of_birth',          # Дата рождения 📅
            'place_of_residence',     # Место проживания 🏠
            'organization',           # Организация 🏢
            'subdivision',            # Подразделение 🏭
            'department',             # Отдел 📂
            'position',               # Должность 👔
            'height',                 # Рост 📏
            'clothing_size',          # Размер одежды 👕
            'shoe_size',              # Размер обуви 👞
            'is_contractor'           # Договор подряда? 📄
        ]
        widgets = {
            # Виджет для организации с автодополнением Select2
            'organization': autocomplete.ModelSelect2(
                url='directory:organization-autocomplete',
                attrs={
                    'data-placeholder': '🏢 Выберите организацию...',
                    'class': 'select2 form-control',
                    'data-theme': 'bootstrap4'
                }
            ),
            # Виджет для подразделения (зависит от организации)
            'subdivision': autocomplete.ModelSelect2(
                url='directory:subdivision-autocomplete',
                forward=['organization'],
                attrs={
                    'data-placeholder': '🏭 Выберите подразделение...',
                    'class': 'select2 form-control',
                    'data-theme': 'bootstrap4'
                }
            ),
            # Виджет для отдела (зависит от подразделения)
            'department': autocomplete.ModelSelect2(
                url='directory:department-autocomplete',
                forward=['subdivision'],
                attrs={
                    'data-placeholder': '📂 Выберите отдел...',
                    'class': 'select2 form-control',
                    'data-theme': 'bootstrap4'
                }
            ),
            # Виджет для должности (зависит от организации, подразделения, отдела)
            'position': autocomplete.ModelSelect2(
                url='directory:position-autocomplete',
                forward=['organization', 'subdivision', 'department'],
                attrs={
                    'data-placeholder': '👔 Выберите должность...',
                    'class': 'select2 form-control',
                    'data-theme': 'bootstrap4'
                }
            ),
            # Виджет для даты рождения
            'date_of_birth': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'},
                format='%Y-%m-%d'
            ),
            # Виджет для места проживания (многострочное поле)
            'place_of_residence': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': '🏠 Введите место проживания...'
                }
            ),
            # Рост
            'height': forms.Select(
                attrs={'class': 'form-control'}
            ),
            # Размер одежды
            'clothing_size': forms.Select(
                attrs={'class': 'form-control'}
            ),
            # Размер обуви
            'shoe_size': forms.Select(
                attrs={'class': 'form-control'}
            ),
        }

    def __init__(self, *args, **kwargs):
        # 🔑 Извлекаем пользователя, если он передан
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # 🎨 Настройка crispy-forms для красивой верстки
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', '💾 Принять'))

        # 🔒 Дополнительная настройка для начального значения организации
        # (если у пользователя только одна организация)
        if self.user and hasattr(self.user, 'profile'):
            user_orgs = self.user.profile.organizations.all()
            if user_orgs.count() == 1:
                self.initial['organization'] = user_orgs.first().id