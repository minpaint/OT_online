# 📂 deadline_control/admin/medical_examination.py

import logging
from datetime import timedelta
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.db.models import Exists, OuterRef
from django.utils import timezone
from django.utils.html import format_html
from django.http import HttpResponseRedirect

from deadline_control.models import (
    MedicalExaminationType,
    HarmfulFactor,
    MedicalSettings,
    MedicalExaminationNorm,
    PositionMedicalFactor,
    EmployeeMedicalExamination,
)
from deadline_control.forms.medical_examination import (
    PositionNormForm,
    HarmfulFactorNormFormSet,
    HarmfulFactorNormForm,
)
from directory.models.position import Position

# Настройка логирования
logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# 🔧 Справочники
# ------------------------------------------------------------------

@admin.register(MedicalExaminationType)
class MedicalExaminationTypeAdmin(admin.ModelAdmin):
    """Админка для типов медосмотров"""
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(HarmfulFactor)
class HarmfulFactorAdmin(admin.ModelAdmin):
    list_display = ("short_name", "full_name", "periodicity")
    search_fields = ("short_name", "full_name",)

    change_list_template = "admin/deadline_control/harmful_factor/change_list.html"

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('import/', self.import_view, name='deadline_control_harmfulfactor_import'),
            path('export/', self.export_view, name='deadline_control_harmfulfactor_export'),
        ]
        return custom_urls + urls

    def import_view(self, request):
        """Импорт вредных факторов"""
        from django.shortcuts import render, redirect
        from django.contrib import messages
        from tablib import Dataset
        from directory.resources.harmful_factor import HarmfulFactorResource

        context = self.admin_site.each_context(request)

        if request.method == 'POST':
            if "confirm" in request.POST:
                dataset_data = request.session.get("harmful_factor_dataset")
                if not dataset_data:
                    messages.error(request, "Сессия с набором данных не найдена. Загрузите файл снова.")
                    return redirect("admin:deadline_control_harmfulfactor_import")

                dataset = Dataset().load(dataset_data)
                resource = HarmfulFactorResource()
                result = resource.import_data(dataset, dry_run=False)

                del request.session["harmful_factor_dataset"]

                if result.has_errors():
                    messages.error(request, f"⚠ Импорт завершён с ошибками! Новых: {result.totals['new']}, ошибок: {result.totals['error']}")
                else:
                    messages.success(request, f"✔ Импорт завершён! Новых: {result.totals['new']}, обновлено: {result.totals['update']}")
                return redirect("admin:deadline_control_harmfulfactor_changelist")
            else:
                import_file = request.FILES.get("import_file")
                if not import_file:
                    messages.error(request, "Файл не выбран")
                    return redirect("admin:deadline_control_harmfulfactor_import")

                file_format = import_file.name.split('.')[-1].lower()
                if file_format not in ["xlsx", "xls"]:
                    messages.error(request, "Поддерживаются только файлы XLSX и XLS")
                    return redirect("admin:deadline_control_harmfulfactor_import")

                try:
                    dataset = Dataset().load(import_file.read(), format=file_format)
                    resource = HarmfulFactorResource()
                    result = resource.import_data(dataset, dry_run=True)

                    request.session["harmful_factor_dataset"] = dataset.export("json")

                    context.update({
                        "title": "Предпросмотр импорта вредных факторов",
                        "result": result,
                        "dataset": dataset,
                    })
                    return render(request, "admin/deadline_control/harmful_factor/import_preview.html", context)
                except Exception as e:
                    messages.error(request, f"Ошибка при обработке файла: {str(e)}")
                    return redirect("admin:deadline_control_harmfulfactor_import")

        context.update({
            "title": "Импорт вредных факторов",
            "subtitle": None,
        })
        return render(request, "admin/deadline_control/harmful_factor/import.html", context)
    def export_view(self, request):
        """📤 Экспорт вредных факторов"""
        from django.http import HttpResponse
        from directory.resources.harmful_factor import HarmfulFactorResource

        resource = HarmfulFactorResource()
        dataset = resource.export()
        response = HttpResponse(dataset.xlsx, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="harmful_factors.xlsx"'
        return response


@admin.register(MedicalSettings)
class MedicalSettingsAdmin(admin.ModelAdmin):
    list_display = ("organization", "days_before_issue", "days_before_email", "has_template")
    list_filter = ("organization",)
    search_fields = ("organization__short_name_ru", "organization__full_name_ru")

    fieldsets = (
        ('Организация', {
            'fields': ('organization',)
        }),
        ('Уведомления', {
            'fields': ('days_before_issue', 'days_before_email')
        }),
        ('Шаблоны документов', {
            'fields': ('referral_template',),
            'description': '<strong>Шаблон направления на медосмотр (необязательно):</strong><br>'
                          '• Если шаблон НЕ загружен - используется <strong>эталонный шаблон</strong> системы<br>'
                          '• Если шаблон загружен - будет использоваться <strong>ваш шаблон</strong> для этой организации<br>'
                          '• Формат: DOCX с переменными docxtpl'
        }),
    )

    def has_template(self, obj):
        return bool(obj.referral_template)
    has_template.boolean = True
    has_template.short_description = "Шаблон загружен"

    def get_queryset(self, request):
        """Фильтруем по организациям пользователя"""
        qs = super().get_queryset(request)
        if not request.user.is_superuser and hasattr(request.user, 'profile'):
            allowed_orgs = request.user.profile.organizations.all()
            qs = qs.filter(organization__in=allowed_orgs)
        return qs.select_related('organization')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Показываем только организации, доступные пользователю"""
        if db_field.name == "organization":
            if not request.user.is_superuser and hasattr(request.user, 'profile'):
                kwargs["queryset"] = request.user.profile.organizations.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# ------------------------------------------------------------------
# 📑 Эталонные нормы — древовидное представление
# ------------------------------------------------------------------

@admin.register(MedicalExaminationNorm)
class MedicalExaminationNormAdmin(admin.ModelAdmin):
    change_list_template = "admin/directory/medicalnorm/change_list_tree.html"

    list_display = ("position_name", "harmful_factor", "periodicity")
    list_filter = ("harmful_factor",)
    search_fields = ("position_name",)

    # Отключаем стандартное добавление - используем только add_multiple
    def has_add_permission(self, request):
        return False

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('add-multiple/', self.add_multiple_view, name='deadline_control_medicalexaminationnorm_add_multiple'),
        ]
        return custom_urls + urls

    def add_multiple_view(self, request):
        """
        View для добавления/редактирования множественных вредных факторов к профессии
        """
        from django.shortcuts import render, redirect
        from django.contrib import messages
        from django.forms import formset_factory

        context = self.admin_site.each_context(request)

        # Получаем position_id из GET параметров
        position_id = request.GET.get('position')
        initial_position_name = ''
        existing_norms = []

        # Если передан position_id, загружаем существующие нормы
        if position_id:
            try:
                position = Position.objects.get(pk=position_id)
                initial_position_name = position.position_name
                # Загружаем существующие нормы для этой профессии
                existing_norms = MedicalExaminationNorm.objects.filter(
                    position_name=initial_position_name
                ).select_related('harmful_factor')
            except Position.DoesNotExist:
                pass

        if request.method == 'POST':
            position_form = PositionNormForm(request.POST)
            formset = HarmfulFactorNormFormSet(request.POST)

            if position_form.is_valid() and formset.is_valid():
                position_name = position_form.cleaned_data['position_name']
                created_count = 0
                deleted_count = 0

                # Собираем список факторов, которые должны остаться
                factors_to_keep = set()

                for form in formset:
                    if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                        harmful_factor = form.cleaned_data.get('harmful_factor')
                        if harmful_factor:
                            factors_to_keep.add(harmful_factor.id)

                            # Проверяем, существует ли уже такая норма
                            existing = MedicalExaminationNorm.objects.filter(
                                position_name=position_name,
                                harmful_factor=harmful_factor
                            ).first()

                            if existing:
                                # Обновляем существующую норму
                                existing.periodicity_override = form.cleaned_data.get('periodicity_override')
                                existing.notes = form.cleaned_data.get('notes', '')
                                existing.save()
                            else:
                                # Создаём новую норму
                                MedicalExaminationNorm.objects.create(
                                    position_name=position_name,
                                    harmful_factor=harmful_factor,
                                    periodicity_override=form.cleaned_data.get('periodicity_override'),
                                    notes=form.cleaned_data.get('notes', '')
                                )
                                created_count += 1

                # Удаляем нормы, которые были отмечены на удаление
                for form in formset:
                    if form.cleaned_data and form.cleaned_data.get('DELETE', False):
                        harmful_factor = form.cleaned_data.get('harmful_factor')
                        if harmful_factor:
                            deleted = MedicalExaminationNorm.objects.filter(
                                position_name=position_name,
                                harmful_factor=harmful_factor
                            ).delete()
                            if deleted[0] > 0:
                                deleted_count += 1

                msg_parts = []
                if created_count > 0:
                    msg_parts.append(f'создано: {created_count}')
                if deleted_count > 0:
                    msg_parts.append(f'удалено: {deleted_count}')

                if msg_parts:
                    messages.success(request, f'✅ Изменения сохранены ({", ".join(msg_parts)})')
                else:
                    messages.info(request, 'Изменений не было')

                return redirect('admin:deadline_control_medicalexaminationnorm_changelist')
        else:
            # Инициализация форм
            position_form = PositionNormForm(initial={'position_name': initial_position_name})

            # Формируем initial data для formset из существующих норм
            initial_data = []
            for norm in existing_norms:
                initial_data.append({
                    'harmful_factor': norm.harmful_factor,
                    'periodicity_override': norm.periodicity_override,
                    'notes': norm.notes,
                })

            # Создаём formset с нужным количеством extra форм
            if initial_data:
                # Если есть существующие данные, показываем их + 1 пустую форму
                CustomFormSet = formset_factory(
                    HarmfulFactorNormForm,
                    extra=1,
                    can_delete=True
                )
                formset = CustomFormSet(initial=initial_data)
            else:
                # Если нет данных, показываем 1 пустую форму
                formset = HarmfulFactorNormFormSet()

        context.update({
            'title': 'Редактировать вредные факторы профессии' if existing_norms else 'Добавить вредные факторы для профессии',
            'position_form': position_form,
            'formset': formset,
            'opts': self.model._meta,
            'existing_norms': existing_norms,
        })

        return render(request, 'admin/directory/medicalnorm/add_multiple.html', context)

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
            ).select_related("harmful_factor")

            # Проверяем, есть ли переопределения
            has_overrides = name in overridden_professions

            # Находим эталонную (первую) должность с таким названием
            reference_position = Position.objects.filter(position_name=name).first()

            professions.append({
                "name": name,
                "norms": norms,
                "has_overrides": has_overrides,
                "reference_position": reference_position  # Добавляем ссылку на эталонную должность
            })

        extra_context["professions"] = professions
        return super().changelist_view(request, extra_context)


# ------------------------------------------------------------------
# 👨‍⚕️ Журнал медосмотров сотрудников
# ------------------------------------------------------------------

class DeadlineWindowFilter(SimpleListFilter):
    """Фильтр по сроку: просрочено / скоро / позже / без даты."""
    title = "Срок"
    parameter_name = "deadline_state"

    def lookups(self, request, model_admin):
        return (
            ("overdue", "Просрочено"),
            ("soon", "До 14 дней"),
            ("future", "Больше 14 дней"),
            ("nodate", "Без даты"),
        )

    def queryset(self, request, queryset):
        value = self.value()
        today = timezone.now().date()
        warning_date = today + timedelta(days=14)

        if value == "overdue":
            return queryset.filter(next_date__lt=today)
        if value == "soon":
            return queryset.filter(next_date__gte=today, next_date__lte=warning_date)
        if value == "future":
            return queryset.filter(next_date__gt=warning_date)
        if value == "nodate":
            return queryset.filter(next_date__isnull=True)
        return queryset


@admin.register(EmployeeMedicalExamination)
class EmployeeMedicalExaminationAdmin(admin.ModelAdmin):
    list_display = (
        "employee", "employee_organization", "harmful_factor", "deadline_badge",
    )
    list_filter = (DeadlineWindowFilter, "status", "harmful_factor", "employee__organization")
    search_fields = ("employee__full_name_nominative", "employee__organization__short_name_ru")
    date_hierarchy = "date_completed"
    list_select_related = ("employee", "employee__organization", "harmful_factor")
    ordering = ("next_date",)
    list_per_page = 50

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser and hasattr(request.user, 'profile'):
            allowed_orgs = request.user.profile.organizations.all()
            qs = qs.filter(employee__organization__in=allowed_orgs)
        return qs

    def employee_organization(self, obj):
        org = getattr(obj.employee, "organization", None)
        return org.short_name_ru if org else "-"
    employee_organization.short_description = "Организация"
    employee_organization.admin_order_field = "employee__organization__short_name_ru"

    def deadline_badge(self, obj):
        """Компактный бейдж со сроком и подсветкой."""
        if not obj.next_date:
            return format_html('<span style="background:#9e9e9e;color:white;padding:2px 8px;border-radius:6px;">Без даты</span>')

        days = obj.days_until_next()
        color = "#4caf50"
        label = f"{obj.next_date} · {days} дн."

        if days is None:
            color = "#9e9e9e"
            label = f"{obj.next_date}"
        elif days < 0:
            color = "#f44336"
            label = f"{obj.next_date} · -{abs(days)} дн."
        elif days <= 14:
            color = "#ff9800"
            label = f"{obj.next_date} · {days} дн."

        return format_html(
            '<span style="background:{bg};color:white;padding:2px 8px;border-radius:6px;font-weight:600;">{text}</span>',
            bg=color,
            text=label,
        )

    deadline_badge.short_description = "Срок"
    deadline_badge.admin_order_field = "next_date"

