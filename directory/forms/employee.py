# directory/forms/employee.py
"""
👤 Форма для сотрудников с ограничением по организациям и иерархической фильтрацией

Обеспечивает выбор организации, подразделения, отдела и должности,
при этом данные фильтруются согласно доступным организациям из профиля пользователя. 🚀
"""

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from dal import autocomplete
from directory.models import Employee, StructuralSubdivision, Department, Position
from .mixins import OrganizationRestrictionFormMixin  # Импорт миксина 🚀


class EmployeeForm(OrganizationRestrictionFormMixin, forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            "full_name_nominative", "full_name_dative",
            "date_of_birth", "place_of_residence",
            "organization", "subdivision", "department", "position",
            "height", "clothing_size", "shoe_size",
            "is_contractor"
        ]
        widgets = {
            "organization": autocomplete.ModelSelect2(
                url="directory:organization-autocomplete",
                attrs={
                    "data-placeholder": "🏢 Выберите организацию...",
                    "class": "select2-basic"
                }
            ),
            "subdivision": autocomplete.ModelSelect2(
                url="directory:subdivision-autocomplete",
                forward=["organization"],
                attrs={
                    "data-placeholder": "🏭 Выберите подразделение...",
                    "class": "select2-basic"
                }
            ),
            "department": autocomplete.ModelSelect2(
                url="directory:department-autocomplete",
                forward=["subdivision"],
                attrs={
                    "data-placeholder": "📂 Выберите отдел...",
                    "class": "select2-basic"
                }
            ),
            "position": autocomplete.ModelSelect2(
                url="directory:position-autocomplete",
                forward=["organization", "subdivision", "department"],
                attrs={
                    "data-placeholder": "👔 Выберите должность...",
                    "class": "select2-basic"
                }
            ),
            "date_of_birth": forms.DateInput(
                attrs={"type": "date"},
                format="%Y-%m-%d"
            ),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # 🎨 Настройка crispy-forms
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.add_input(Submit("submit", "💾 Сохранить"))

        # Делам поля subdivision и department необязательными 🔧
        self.fields["subdivision"].required = False
        self.fields["department"].required = False

        # Ограничиваем выбор организаций по профилю пользователя 🔒
        if self.user and hasattr(self.user, "profile"):
            user_orgs = self.user.profile.organizations.all()
            self.fields["organization"].queryset = user_orgs

            # Если у пользователя одна организация – ставим её по умолчанию
            if user_orgs.count() == 1:
                org = user_orgs.first()
                self.initial["organization"] = org.id
                self.fields["subdivision"].queryset = StructuralSubdivision.objects.filter(organization=org)
            else:
                self.fields["subdivision"].queryset = StructuralSubdivision.objects.none()

            # Очищаем зависимые поля
            self.fields["department"].queryset = Department.objects.none()
            self.fields["position"].queryset = Position.objects.none()

    def clean(self):
        """
        🛠 Дополнительные проверки перед сохранением:
        - Если выбрано подразделение, но не выбрана организация, устанавливаем организацию.
        - Если выбрано подразделение, но не указан отдел – очищаем поле department.
        """
        cleaned_data = super().clean()
        organization = cleaned_data.get("organization")
        subdivision = cleaned_data.get("subdivision")
        department = cleaned_data.get("department")

        if subdivision and not organization:
            cleaned_data["organization"] = subdivision.organization

        if subdivision and not department:
            cleaned_data["department"] = None

        return cleaned_data
