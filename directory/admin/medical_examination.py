# D:\YandexDisk\OT_online\directory\admin\medical_examination.py

from django.contrib import admin
from django.db.models import Exists, OuterRef
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
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(HarmfulFactor)
class HarmfulFactorAdmin(admin.ModelAdmin):
    list_display = ("short_name", "full_name", "examination_type", "periodicity")
    list_filter = ("examination_type",)
    search_fields = ("short_name", "full_name",)


@admin.register(MedicalSettings)
class MedicalSettingsAdmin(admin.ModelAdmin):
    list_display = ("days_before_issue", "days_before_email")
    list_editable = ("days_before_issue", "days_before_email")
    list_display_links = None


# ------------------------------------------------------------------
# 📑 Эталонные нормы — древовидное представление
# ------------------------------------------------------------------

@admin.register(MedicalExaminationNorm)
class MedicalExaminationNormAdmin(admin.ModelAdmin):
    form = UniquePositionMedicalNormForm
    change_form_template = "admin/directory/medicalnorm/change_form.html"
    change_list_template = "admin/directory/medicalnorm/change_list_tree.html"

    list_display = ("position_name", "harmful_factor", "periodicity")
    list_filter = ("harmful_factor__examination_type",)
    search_fields = ("position_name",)

    def get_form(self, request, obj=None, **kwargs):
        """
        Если в URL есть ?position=<id>, передаём его в форму,
        чтобы при клике «+» в дереве должность уже была выбрана.
        """
        base_form = super().get_form(request, obj, **kwargs)
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
        Формируем контекст professions = [{ name, norms, has_overrides }, ...],
        чтобы шаблон показывал дерево с индикаторами переопределений.
        """
        extra_context = extra_context or {}

        # Все уникальные имена профессий из норм
        names = MedicalExaminationNorm.objects.values_list(
            "position_name", flat=True
        ).distinct().order_by("position_name")

        # Получаем информацию о профессиях с переопределениями
        overridden_professions = set(
            PositionMedicalFactor.objects.values_list(
                "position__position_name", flat=True
            ).distinct()
        )

        professions = []
        for name in names:
            # Нормы для этой профессии
            norms = MedicalExaminationNorm.objects.filter(
                position_name=name
            ).select_related("harmful_factor__examination_type")

            # Проверяем, есть ли переопределения
            has_overrides = name in overridden_professions

            professions.append({
                "name": name,
                "norms": norms,
                "has_overrides": has_overrides
            })

        extra_context["professions"] = professions
        return super().changelist_view(request, extra_context)


# ------------------------------------------------------------------
# 👨‍⚕️ Журнал медосмотров сотрудников
# ------------------------------------------------------------------

@admin.register(EmployeeMedicalExamination)
class EmployeeMedicalExaminationAdmin(admin.ModelAdmin):
    list_display = (
        "employee", "examination_type", "harmful_factor",
        "date_completed", "next_date", "status"
    )
    list_filter = ("status", "examination_type")
    search_fields = ("employee__full_name_nominative",)
    date_hierarchy = "date_completed"