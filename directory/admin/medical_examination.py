# 📂 directory/admin/medical_examination.py

import logging
from django.contrib import admin
from django.db.models import Exists, OuterRef
from django.utils.html import format_html
from django.http import HttpResponseRedirect

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
from directory.forms.medical_examination import (
    PositionNormForm,
    HarmfulFactorNormFormSet,
)
from directory.models.position import Position

# Настройка логирования
logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# 🔧 Справочники
# ------------------------------------------------------------------

# MedicalExaminationType больше не используется в админке

@admin.register(HarmfulFactor)
class HarmfulFactorAdmin(admin.ModelAdmin):
    list_display = ("short_name", "full_name", "periodicity")
    search_fields = ("short_name", "full_name",)

    change_list_template = "admin/directory/harmful_factor/change_list.html"

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('import/', self.import_view, name='directory_harmfulfactor_import'),
            path('export/', self.export_view, name='directory_harmfulfactor_export'),
        ]
        return custom_urls + urls

    def import_view(self, request):
        """📥 Импорт вредных факторов"""
        from django.shortcuts import render, redirect
        from django.contrib import messages
        from tablib import Dataset
        from directory.resources.harmful_factor import HarmfulFactorResource

        context = self.admin_site.each_context(request)

        if request.method == 'POST':
            if 'confirm' in request.POST:
                # Финальное подтверждение импорта
                dataset_data = request.session.get('harmful_factor_dataset')
                if not dataset_data:
                    messages.error(request, 'Данные для импорта не найдены. Загрузите файл заново.')
                    return redirect('admin:directory_harmfulfactor_import')

                dataset = Dataset().load(dataset_data)
                resource = HarmfulFactorResource()
                result = resource.import_data(dataset, dry_run=False)

                del request.session['harmful_factor_dataset']

                if result.has_errors():
                    messages.error(request, f'❌ Импорт завершен с ошибками! Создано: {result.totals["new"]}, ошибок: {result.totals["error"]}')
                else:
                    messages.success(request, f'✅ Импорт завершен! Создано: {result.totals["new"]}, обновлено: {result.totals["update"]}')
                return redirect('admin:directory_harmfulfactor_changelist')
            else:
                # Предпросмотр импорта
                import_file = request.FILES.get('import_file')
                if not import_file:
                    messages.error(request, 'Файл не выбран')
                    return redirect('admin:directory_harmfulfactor_import')

                file_format = import_file.name.split('.')[-1].lower()
                if file_format not in ['xlsx', 'xls']:
                    messages.error(request, 'Поддерживаются только файлы XLSX и XLS')
                    return redirect('admin:directory_harmfulfactor_import')

                try:
                    dataset = Dataset().load(import_file.read(), format=file_format)
                    resource = HarmfulFactorResource()
                    result = resource.import_data(dataset, dry_run=True)

                    # Сохраняем данные в сессии для финального импорта
                    request.session['harmful_factor_dataset'] = dataset.export('json')

                    context.update({
                        'title': 'Предпросмотр импорта вредных факторов',
                        'result': result,
                        'dataset': dataset,
                    })
                    return render(request, 'admin/directory/harmful_factor/import_preview.html', context)
                except Exception as e:
                    messages.error(request, f'Ошибка при обработке файла: {str(e)}')
                    return redirect('admin:directory_harmfulfactor_import')

        context.update({
            'title': 'Импорт вредных факторов',
            'subtitle': None,
        })
        return render(request, 'admin/directory/harmful_factor/import.html', context)

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
    list_display = ("days_before_issue", "days_before_email")
    list_editable = ("days_before_issue", "days_before_email")
    list_display_links = None


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
            path('add-multiple/', self.add_multiple_view, name='directory_medicalexaminationnorm_add_multiple'),
        ]
        return custom_urls + urls

    def add_multiple_view(self, request):
        """
        View для добавления множественных вредных факторов к профессии
        """
        from django.shortcuts import render, redirect
        from django.contrib import messages

        context = self.admin_site.each_context(request)

        if request.method == 'POST':
            position_form = PositionNormForm(request.POST)
            formset = HarmfulFactorNormFormSet(request.POST)

            if position_form.is_valid() and formset.is_valid():
                position_name = position_form.cleaned_data['position_name']
                created_count = 0

                for form in formset:
                    if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                        harmful_factor = form.cleaned_data.get('harmful_factor')
                        if harmful_factor:
                            # Проверяем, не существует ли уже такая норма
                            existing = MedicalExaminationNorm.objects.filter(
                                position_name=position_name,
                                harmful_factor=harmful_factor
                            ).first()

                            if not existing:
                                MedicalExaminationNorm.objects.create(
                                    position_name=position_name,
                                    harmful_factor=harmful_factor,
                                    periodicity_override=form.cleaned_data.get('periodicity_override'),
                                    notes=form.cleaned_data.get('notes', '')
                                )
                                created_count += 1

                if created_count > 0:
                    messages.success(request, f'✅ Создано норм: {created_count}')
                else:
                    messages.warning(request, 'Нормы не были добавлены (возможно, они уже существуют)')

                return redirect('admin:directory_medicalexaminationnorm_changelist')
        else:
            position_form = PositionNormForm()
            formset = HarmfulFactorNormFormSet()

        context.update({
            'title': 'Добавить вредные факторы для профессии',
            'position_form': position_form,
            'formset': formset,
            'opts': self.model._meta,
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

@admin.register(EmployeeMedicalExamination)
class EmployeeMedicalExaminationAdmin(admin.ModelAdmin):
    list_display = (
        "employee", "harmful_factor",
        "date_completed", "next_date", "status"
    )
    list_filter = ("status", "harmful_factor")
    search_fields = ("employee__full_name_nominative",)
    date_hierarchy = "date_completed"