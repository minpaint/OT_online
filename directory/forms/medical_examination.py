# D:\YandexDisk\OT_online\directory\forms\medical_examination.py
"""
🩺 Формы модуля медицинских осмотров

• Синхронизированы с актуальными моделями.
• Добавлена UniquePositionMedicalNormForm — выбор нормы по общему названию
  профессии (должности) без привязки к организации.
"""

from django import forms
from django.core.validators import FileExtensionValidator
from django.utils import timezone

from directory.models.medical_examination import (
    MedicalExaminationType,
    HarmfulFactor,
    MedicalSettings,
)
from directory.models.medical_norm import (
    MedicalExaminationNorm,
    PositionMedicalFactor,
    EmployeeMedicalExamination,
)
from directory.models.position import Position
from directory.models.employee import Employee

__all__ = [
    # базовые формы
    "MedicalExaminationTypeForm",
    "HarmfulFactorForm",
    "MedicalExaminationNormForm",
    "PositionMedicalFactorForm",
    "EmployeeMedicalExaminationForm",
    "MedicalSettingsForm",
    # поисковые / сервисные
    "MedicalNormSearchForm",
    "EmployeeMedicalExaminationSearchForm",
    "MedicalNormImportForm",
    "MedicalNormExportForm",
    # 🆕 новая
    "UniquePositionMedicalNormForm",
]

# ---------------------------------------------------------------------------
# 📋 ВИДЫ МЕДОСМОТРОВ
# ---------------------------------------------------------------------------

class MedicalExaminationTypeForm(forms.ModelForm):
    class Meta:
        model = MedicalExaminationType
        fields = ["name"]
        widgets = {"name": forms.TextInput(attrs={"class": "form-control"})}

# ---------------------------------------------------------------------------
# ☢️ ВРЕДНЫЕ ФАКТОРЫ
# ---------------------------------------------------------------------------

class HarmfulFactorForm(forms.ModelForm):
    class Meta:
        model = HarmfulFactor
        fields = ["examination_type", "short_name", "full_name", "periodicity"]
        widgets = {
            "examination_type": forms.Select(attrs={"class": "form-control"}),
            "short_name":       forms.TextInput(attrs={"class": "form-control"}),
            "full_name":        forms.TextInput(attrs={"class": "form-control"}),
            "periodicity":      forms.NumberInput(attrs={"class": "form-control"}),
        }

# ---------------------------------------------------------------------------
# 📑 ЭТАЛОННЫЕ НОРМЫ
# ---------------------------------------------------------------------------

class MedicalExaminationNormForm(forms.ModelForm):
    class Meta:
        model = MedicalExaminationNorm
        fields = ["position_name", "harmful_factor", "periodicity_override", "notes"]
        widgets = {
            "position_name":       forms.TextInput(attrs={"class": "form-control"}),
            "harmful_factor":      forms.Select(attrs={"class": "form-control"}),
            "periodicity_override":forms.NumberInput(attrs={"class": "form-control"}),
            "notes":               forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

# ---------------------------------------------------------------------------
# 🔄 ПЕРЕОПРЕДЕЛЕНИЯ ДЛЯ КОНКРЕТНЫХ ДОЛЖНОСТЕЙ
# ---------------------------------------------------------------------------

class PositionMedicalFactorForm(forms.ModelForm):
    class Meta:
        model = PositionMedicalFactor
        fields = ["position", "harmful_factor", "periodicity_override", "is_disabled", "notes"]
        widgets = {
            "position":            forms.Select(attrs={"class": "form-control"}),
            "harmful_factor":      forms.Select(attrs={"class": "form-control"}),
            "periodicity_override":forms.NumberInput(attrs={"class": "form-control"}),
            "is_disabled":         forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "notes":               forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

# ---------------------------------------------------------------------------
# 👨‍⚕️ ЖУРНАЛ МЕДОСМОТРОВ СОТРУДНИКОВ
# ---------------------------------------------------------------------------

class EmployeeMedicalExaminationForm(forms.ModelForm):
    class Meta:
        model = EmployeeMedicalExamination
        fields = [
            "employee", "examination_type", "harmful_factor",
            "date_completed", "next_date", "medical_certificate",
            "status", "notes",
        ]
        widgets = {
            "employee":            forms.Select(attrs={"class": "form-control"}),
            "examination_type":    forms.Select(attrs={"class": "form-control"}),
            "harmful_factor":      forms.Select(attrs={"class": "form-control"}),
            "date_completed":      forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "next_date":           forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "medical_certificate": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "status":              forms.Select(attrs={"class": "form-control"}),
            "notes":               forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def clean(self):
        cd = super().clean()
        d1, d2 = cd.get("date_completed"), cd.get("next_date")
        if d1 and d2 and d2 <= d1:
            self.add_error("next_date", "Дата следующего медосмотра должна быть позже даты прохождения")
        if d1 and d1 > timezone.now().date():
            self.add_error("date_completed", "Дата прохождения не может быть в будущем")
        return cd

# ---------------------------------------------------------------------------
# ⚙️ НАСТРОЙКИ
# ---------------------------------------------------------------------------

class MedicalSettingsForm(forms.ModelForm):
    class Meta:
        model = MedicalSettings
        fields = ["days_before_issue", "days_before_email"]
        widgets = {
            "days_before_issue": forms.NumberInput(attrs={"class": "form-control"}),
            "days_before_email": forms.NumberInput(attrs={"class": "form-control"}),
        }

# ---------------------------------------------------------------------------
# 🔍 ПОИСКОВЫЕ / СЕРВИСНЫЕ ФОРМЫ
# ---------------------------------------------------------------------------

class MedicalNormSearchForm(forms.Form):
    position_name = forms.CharField(required=False, label="Наименование должности",
                                    widget=forms.TextInput(attrs={"class": "form-control"}))
    examination_type = forms.ModelChoiceField(required=False, label="Вид медосмотра",
                                              queryset=MedicalExaminationType.objects.all(),
                                              widget=forms.Select(attrs={"class": "form-control"}))
    harmful_factor = forms.CharField(required=False, label="Вредный фактор",
                                     widget=forms.TextInput(attrs={"class": "form-control"}))


class EmployeeMedicalExaminationSearchForm(forms.Form):
    employee = forms.CharField(required=False, label="Сотрудник",
                               widget=forms.TextInput(attrs={"class": "form-control"}))
    examination_type = forms.ModelChoiceField(required=False, label="Вид медосмотра",
                                              queryset=MedicalExaminationType.objects.all(),
                                              widget=forms.Select(attrs={"class": "form-control"}))
    status = forms.ChoiceField(required=False, label="Статус",
                               choices=[("", "---")] + list(EmployeeMedicalExamination.STATUS_CHOICES),
                               widget=forms.Select(attrs={"class": "form-control"}))
    date_from = forms.DateField(required=False, label="Дата с",
                                widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}))
    date_to = forms.DateField(required=False, label="Дата по",
                              widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}))

# импорт / экспорт

class MedicalNormImportForm(forms.Form):
    file = forms.FileField(label="Файл для импорта",
                           validators=[FileExtensionValidator(allowed_extensions=["xls", "xlsx", "csv"])],
                           widget=forms.FileInput(attrs={"class": "form-control"}))
    skip_first_row = forms.BooleanField(required=False, initial=True,
                                        label="Пропустить первую строку",
                                        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}))
    update_existing = forms.BooleanField(required=False, initial=True,
                                         label="Обновлять существующие",
                                         widget=forms.CheckboxInput(attrs={"class": "form-check-input"}))


class MedicalNormExportForm(forms.Form):
    FORMAT_CHOICES = [("xlsx", "Excel (.xlsx)"), ("csv", "CSV (.csv)"), ("json", "JSON (.json)")]
    format = forms.ChoiceField(label="Формат", choices=FORMAT_CHOICES, initial="xlsx",
                               widget=forms.Select(attrs={"class": "form-control"}))
    include_headers = forms.BooleanField(required=False, initial=True,
                                         label="Включить заголовки",
                                         widget=forms.CheckboxInput(attrs={"class": "form-check-input"}))

# ---------------------------------------------------------------------------
# 🆕 ФОРМА ВЫБОРА ОБЩЕЙ ДОЛЖНОСТИ
# ---------------------------------------------------------------------------

class UniquePositionMedicalNormForm(forms.ModelForm):
    """
    Используется в админке MedicalExaminationNormAdmin: выбор «Профессия (должность)»
    из уникальных Position.position_name.  При сохранении заполняет `position_name`.
    """
    unique_position_name = forms.ChoiceField(
        label="Профессия (должность)",
        required=True,
        help_text="Выберите общее название без привязки к организации",
    )

    class Meta:
        model = MedicalExaminationNorm
        fields = ("harmful_factor", "periodicity_override", "notes")
        widgets = {
            "harmful_factor":      forms.Select(attrs={"class": "form-control"}),
            "periodicity_override":forms.NumberInput(attrs={"class": "form-control"}),
            "notes":               forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    # заполнение choices + предустановка
    def __init__(self, *args, **kwargs):
        position_id = kwargs.pop("position_id", None)
        super().__init__(*args, **kwargs)

        names = Position.objects.values_list("position_name", flat=True).distinct().order_by("position_name")
        self.fields["unique_position_name"].choices = [("", "---")] + [(n, n) for n in names]

        if self.instance.pk:
            self.fields["unique_position_name"].initial = self.instance.position_name
        elif position_id:
            try:
                pos = Position.objects.get(pk=position_id)
                self.fields["unique_position_name"].initial = pos.position_name
            except Position.DoesNotExist:
                pass

    # проверяем уникальность (position_name + factor)
    def clean(self):
        cleaned = super().clean()
        name = cleaned.get("unique_position_name")
        factor = cleaned.get("harmful_factor")
        if not name:
            self.add_error("unique_position_name", "Необходимо выбрать должность")
            return cleaned

        qs = MedicalExaminationNorm.objects.filter(position_name=name, harmful_factor=factor)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            self.add_error("unique_position_name", f"Норма для «{name}» и этого фактора уже существует")
        return cleaned

    def save(self, commit=True):
        self.instance.position_name = self.cleaned_data["unique_position_name"]
        return super().save(commit)
