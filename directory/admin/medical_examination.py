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
from directory.models.position import Position
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
        Обрабатываем параметры из запроса: position или position_name
        """
        base_form = super().get_form(request, obj, **kwargs)

        # Обрабатываем прямой ID должности
        position_id = request.GET.get("position")

        # Обрабатываем также имя должности, если ID отсутствует
        position_name = request.GET.get("position_name")

        if position_id or position_name:
            class FormWithPosition(base_form):
                def __new__(cls, *args, **kw):
                    if position_id:
                        kw["position_id"] = position_id
                    elif position_name:
                        # Ищем эталонную должность для имени
                        try:
                            reference_position = Position.objects.filter(
                                position_name=position_name
                            ).order_by('organization__full_name_ru').first()

                            if reference_position:
                                kw["position_id"] = reference_position.id
                        except:
                            pass

                    return base_form(*args, **kw)

            return FormWithPosition

        return base_form

    def _get_profession_icon(self, position_name):
        """
        Определяет эмоджи для профессии на основе её названия
        """
        position_name_lower = position_name.lower()

        # Словарь с эмоджи для разных категорий профессий
        profession_icons = {
            'директор': '👨‍💼',
            'директр': '👨‍💼',  # Для опечаток
            'начальник': '👨‍💼',
            'зам': '👨‍💼',
            'руководител': '👨‍💼',
            'генеральный': '👔',
            'главный': '👔',
            'бухгалтер': '💼',
            'экономист': '📊',
            'финанс': '💰',
            'юрист': '⚖️',
            'адвокат': '⚖️',
            'инженер': '👷‍♂️',
            'техник': '🔧',
            'механик': '🔧',
            'строител': '🏗️',
            'электрик': '⚡',
            'электромонтер': '⚡',
            'сварщик': '🔥',
            'слесарь': '🔨',
            'водитель': '🚗',
            'шофер': '🚗',
            'тракторист': '🚜',
            'программист': '💻',
            'разработчик': '💻',
            'it': '💻',
            'врач': '👨‍⚕️',
            'медсестра': '👩‍⚕️',
            'фельдшер': '🩺',
            'учитель': '👨‍🏫',
            'преподаватель': '👨‍🏫',
            'повар': '👨‍🍳',
            'кондитер': '🍰',
            'пекарь': '🍞',
            'охранник': '👮',
            'секретар': '📝',
            'менеджер': '📋',
            'кладовщик': '📦',
            'уборщи': '🧹',
            'грузчик': '📦',
            'разнорабочий': '🛠️',
        }

        # Ищем соответствие в словаре
        for key, icon in profession_icons.items():
            if key in position_name_lower:
                return icon

        # Возвращаем дефолтную иконку, если ничего не нашли
        return '👔'

    def changelist_view(self, request, extra_context=None):
        """
        Формируем контекст professions = [{ name, reference_position, norms, icon }, ...],
        чтобы шаблон показывал дерево с эмоджи и правильной передачей ID должности.
        Показываем ТОЛЬКО эталонные нормы медосмотров.
        """
        extra_context = extra_context or {}

        # Получаем только уникальные имена должностей из ЭТАЛОННЫХ норм
        # Это гарантирует, что мы не будем показывать переопределенные нормы
        names = MedicalExaminationNorm.objects.values_list(
            "position_name", flat=True
        ).distinct().order_by("position_name")

        professions = []
        for name in names:
            # Получаем только эталонные нормы для этой должности
            norms = MedicalExaminationNorm.objects.filter(
                position_name=name
            ).select_related("harmful_factor", "harmful_factor__examination_type")

            # Находим эталонную должность для правильной ссылки "Добавить"
            reference_position = Position.objects.filter(
                position_name=name
            ).order_by('organization__full_name_ru').first()

            # Определяем эмоджи для профессии
            icon = self._get_profession_icon(name)

            # Добавляем данные в список профессий
            professions.append({
                "name": name,
                "reference_position": reference_position,
                "norms": norms,
                "icon": icon
            })

        extra_context["professions"] = professions
        return super().changelist_view(request, extra_context)


# ------------------------------------------------------------------
# 🔄 Переопределения для должностей — древовидное представление
# ------------------------------------------------------------------

@admin.register(PositionMedicalFactor)
class PositionMedicalFactorAdmin(admin.ModelAdmin):
    change_list_template = "admin/directory/medicalnorm/change_list_tree.html"

    list_display = ("position", "harmful_factor", "periodicity", "is_disabled")
    list_filter = ("is_disabled", "harmful_factor__examination_type")
    search_fields = ("position__position_name",)

    def get_form(self, request, obj=None, **kwargs):
        """
        Аналогично нормам медосмотров — если есть ?position=<id>,
        передаём его в форму, чтобы dropdown «должность» был уже выбран.
        """
        base_form = super().get_form(request, obj, **kwargs)
        position_id = request.GET.get("position")

        if position_id:
            class FormWithPosition(base_form):
                def __new__(cls, *args, **kw):
                    kw["position_id"] = position_id
                    return base_form(*args, **kw)

            return FormWithPosition

        return base_form

    def changelist_view(self, request, extra_context=None):
        """
        Формируем professions = [{ name, reference_position, norms, icon }, ...],
        где norms — ТОЛЬКО переопределенные факторы (PositionMedicalFactor) для этой общей должности.
        """
        extra_context = extra_context or {}

        # Получаем уникальные имена должностей из переопределенных норм
        names = PositionMedicalFactor.objects.values_list(
            "position__position_name", flat=True
        ).distinct().order_by("position__position_name")

        professions = []
        for name in names:
            # Получаем только переопределенные факторы
            factors = PositionMedicalFactor.objects.filter(
                position__position_name=name
            ).select_related("position", "harmful_factor", "harmful_factor__examination_type")

            # Получаем эталонную должность для этого имени
            reference_position = Position.objects.filter(
                position_name=name
            ).order_by('organization__full_name_ru').first()

            # Используем тот же метод для определения иконки, что и в MedicalExaminationNormAdmin
            icon = MedicalExaminationNormAdmin._get_profession_icon(
                MedicalExaminationNormAdmin, name
            )

            # Добавляем данные в список профессий
            professions.append({
                "name": name,
                "reference_position": reference_position,
                "norms": factors,
                "icon": icon
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