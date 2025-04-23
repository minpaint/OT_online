# D:\YandexDisk\OT_online\directory\admin\medical_examination.py

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

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
from directory.forms.medical_examination import UniquePositionMedicalNormForm


# ------------------------------------------------------------------
# 🔧 Справочники
# ------------------------------------------------------------------

@admin.register(MedicalExaminationType)
class MedicalExaminationTypeAdmin(admin.ModelAdmin):
    list_display  = ("name",)
    search_fields = ("name",)


@admin.register(HarmfulFactor)
class HarmfulFactorAdmin(admin.ModelAdmin):
    list_display  = ("short_name", "full_name", "examination_type", "periodicity")
    list_filter   = ("examination_type",)
    search_fields = ("short_name", "full_name",)


@admin.register(MedicalSettings)
class MedicalSettingsAdmin(admin.ModelAdmin):
    list_display       = ("days_before_issue", "days_before_email")
    list_editable      = ("days_before_issue", "days_before_email")
    list_display_links = None  # Чтобы E124 больше не возникало


# ------------------------------------------------------------------
# 📑 Эталонные нормы — древовидное представление
# ------------------------------------------------------------------

@admin.register(MedicalExaminationNorm)
class MedicalExaminationNormAdmin(admin.ModelAdmin):
    form                   = UniquePositionMedicalNormForm
    change_form_template   = "admin/directory/medicalnorm/change_form.html"
    change_list_template   = "admin/directory/medicalnorm/change_list_tree.html"

    list_display  = ("position_name", "harmful_factor", "periodicity")
    list_filter   = ("harmful_factor__examination_type",)
    search_fields = ("position_name",)

    def get_form(self, request, obj=None, **kwargs):
        """
        Если в URL есть ?position=<id>, передаём его в форму,
        чтобы при клике «+» в дереве должность уже была выбрана.
        """
        base_form   = super().get_form(request, obj, **kwargs)
        position_id = request.GET.get("position")
        if position_id:
            class _Wrapper(base_form):
                def __new__(cls, *args, **kw):
                    kw["position_id"] = position_id
                    return base_form(*args, **kw)
            return _Wrapper
        return base_form

    def changelist_view(self, request, extra_context=None):
        """
        Формируем контекст professions = [{ name, norms }, ...],
        чтобы шаблон показывал дерево:
          • позиция (общая)
            └ список норм (строки таблицы)
        """
        extra_context = extra_context or {}
        names = MedicalExaminationNorm.objects.values_list(
            "position_name", flat=True
        ).distinct().order_by("position_name")

        professions = []
        for name in names:
            norms = MedicalExaminationNorm.objects.filter(
                position_name=name
            ).select_related("harmful_factor__examination_type")
            professions.append({
                "name": name,
                "norms": norms
            })

        extra_context["professions"] = professions
        return super().changelist_view(request, extra_context)


# ------------------------------------------------------------------
# 🔄 Переопределения для должностей — древовидное представление
# ------------------------------------------------------------------

@admin.register(PositionMedicalFactor)
class PositionMedicalFactorAdmin(admin.ModelAdmin):
    change_list_template = "admin/directory/medicalnorm/change_list_tree.html"

    list_display  = ("position", "harmful_factor", "periodicity", "is_disabled")
    list_filter   = ("is_disabled", "harmful_factor__examination_type")
    search_fields = ("position__position_name",)

    def get_form(self, request, obj=None, **kwargs):
        """
        Аналогично нормам медосмотров — если есть ?position=<id>,
        передаём его в форму, чтобы dropdown «должность» был уже выбран.
        """
        base_form   = super().get_form(request, obj, **kwargs)
        position_id = request.GET.get("position")
        if position_id:
            class _Wrapper(base_form):
                def __new__(cls, *args, **kw):
                    kw["position_id"] = position_id
                    return base_form(*args, **kw)
            return _Wrapper
        return base_form

    def changelist_view(self, request, extra_context=None):
        """
        Формируем professions = [{ name, norms }, ...],
        где norms — PositionMedicalFactor для этой общей должности.
        """
        extra_context = extra_context or {}
        names = PositionMedicalFactor.objects.values_list(
            "position__position_name", flat=True
        ).distinct().order_by("position__position_name")

        professions = []
        for name in names:
            factors = PositionMedicalFactor.objects.filter(
                position__position_name=name
            ).select_related("position", "harmful_factor__examination_type")
            professions.append({
                "name": name,
                "norms": factors
            })

        extra_context["professions"] = professions
        return super().changelist_view(request, extra_context)


# ------------------------------------------------------------------
# 👨‍⚕️ Журнал медосмотров сотрудников
# ------------------------------------------------------------------

@admin.register(EmployeeMedicalExamination)
class EmployeeMedicalExaminationAdmin(admin.ModelAdmin):
    list_display   = (
        "employee", "examination_type", "harmful_factor",
        "date_completed", "next_date", "status"
    )
    list_filter    = ("status", "examination_type")
    search_fields  = ("employee__full_name_nominative",)
    date_hierarchy = "date_completed"
