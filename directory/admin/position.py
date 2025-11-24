# directory/admin/position.py
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils.html import format_html
from django.db.models import Exists, OuterRef, Count
from django.http import HttpResponse
from tablib import Dataset

from directory.models import Position
from directory.forms.position import PositionForm
from directory.admin.mixins.tree_view import TreeViewMixin
from directory.models.siz import SIZNorm, SIZ
from deadline_control.models.medical_norm import PositionMedicalFactor, MedicalExaminationNorm
from deadline_control.models.medical_examination import HarmfulFactor
from directory.models.commission import CommissionMember
from directory.utils.profession_icons import get_profession_icon
from directory.resources.organization_structure import OrganizationStructureResource


# Обновленный инлайн для СИЗ
class SIZNormInlineForPosition(admin.TabularInline):
    """📋 Встроенные нормы СИЗ для должности с отображением всех полей"""
    model = SIZNorm
    extra = 3  # Показываем 3 пустые строки для быстрого добавления нескольких СИЗ
    fields = ('siz', 'classification', 'unit', 'quantity', 'wear_period', 'condition', 'order')
    readonly_fields = ('classification', 'unit', 'wear_period')
    verbose_name = "Норма СИЗ"
    verbose_name_plural = "Нормы СИЗ"

    # Восстанавливаем autocomplete_fields с добавлением формы
    autocomplete_fields = ['siz']

    # Предотвращаем отображение слишком много пустых форм
    def get_extra(self, request, obj=None, **kwargs):
        """Возвращает 3 пустые строки для добавления новых СИЗ"""
        return 3

    # Улучшаем фильтрацию запросов
    def get_queryset(self, request):
        # Все нормы для должности, отсортированные по условию и порядку
        # Исключаем пустые нормы (без указанного СИЗ)
        return super().get_queryset(request).select_related('siz').filter(
            siz__isnull=False
        ).order_by('condition', 'order')

    def classification(self, obj):
        """📊 Отображение классификации СИЗ"""
        return obj.siz.classification if obj.siz else ""

    classification.short_description = "Классификация"

    def unit(self, obj):
        """📏 Отображение единицы измерения СИЗ"""
        return obj.siz.unit if obj.siz else ""

    unit.short_description = "Ед. изм."

    def wear_period(self, obj):
        """⌛ Отображение срока носки СИЗ"""
        if obj.siz:
            if obj.siz.wear_period == 0:
                return "До износа"
            return f"{obj.siz.wear_period} мес."
        return ""

    wear_period.short_description = "Срок носки"

    def formfield_for_dbfield(self, db_field, **kwargs):
        """Настройка полей формы"""
        form_field = super().formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == 'quantity':
            form_field.widget.attrs['style'] = 'width: 80px;'
        if db_field.name == 'condition':
            form_field.widget.attrs['style'] = 'width: 200px;'
        if db_field.name == 'order':
            form_field.widget.attrs['style'] = 'width: 60px;'
        # Добавляем стили для виджета siz, если он уже настроен
        if db_field.name == 'siz' and hasattr(form_field.widget, 'attrs'):
            form_field.widget.attrs['style'] = 'min-width: 260px;'
            form_field.widget.attrs['class'] = 'select2-siz-field'
        return form_field


# Новый инлайн для вредных факторов медосмотров
class PositionMedicalFactorInline(admin.TabularInline):
    """🏥 Встроенные вредные факторы для должности"""
    model = PositionMedicalFactor
    extra = 0
    # Удалено поле notes из списка полей
    fields = ('harmful_factor', 'periodicity', 'periodicity_override', 'is_disabled')
    readonly_fields = ('periodicity',)
    verbose_name = "Вредный фактор медосмотра"
    verbose_name_plural = "Вредные факторы медосмотров"
    autocomplete_fields = ['harmful_factor']

    def get_extra(self, request, obj=None, **kwargs):
        """Возвращает 0 для существующих объектов, 1 для новых"""
        return 0 if obj else 1

    def get_queryset(self, request):
        """Оптимизированный запрос"""
        return super().get_queryset(request).select_related(
            'harmful_factor'
        ).filter(
            harmful_factor__isnull=False
        ).order_by('harmful_factor__short_name')

    def periodicity(self, obj):
        """⏱️ Отображение базовой периодичности"""
        if obj.harmful_factor:
            return f"{obj.harmful_factor.periodicity} мес."
        return ""

    periodicity.short_description = "Базовая периодичность"

    def formfield_for_dbfield(self, db_field, **kwargs):
        """Настройка полей формы"""
        form_field = super().formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == 'periodicity_override':
            form_field.widget.attrs['style'] = 'width: 80px;'
        return form_field


@admin.register(Position)
class PositionAdmin(TreeViewMixin, admin.ModelAdmin):
    """
    👔 Админ-класс для модели Position.

    Реализует древовидное представление должностей с индикаторами:
    - Наличия норм СИЗ (🛡️) - проверяет сначала переопределенные, затем эталонные
    - Наличия медосмотров (🏥) - проверяет сначала переопределенные, затем эталонные
    - Роли в комиссиях (определяется через связь с CommissionMember)
    - Прочих атрибутов должности (ответственный за ОТ, ЭБ и др.)
    """
    form = PositionForm
    # Путь к шаблону для древовидного отображения
    change_list_template = "admin/directory/position/change_list_tree.html"
    # Шаблон формы для добавления кнопки подтягивания норм
    change_form_template = "admin/directory/position/change_form.html"

    # Определяем порядок полей в форме
    fieldsets = (
        ('Основная информация', {
            'fields': (
                'position_name',
                'organization',
                'subdivision',
                'department',
                'is_responsible_for_safety',
                'can_be_internship_leader',
                'can_sign_orders',
                'is_electrical_personnel',
            )
        }),
        ('Документация', {
            'fields': (
                'contract_work_name',
                'safety_instructions_numbers',
                'contract_safety_instructions',
                'electrical_safety_group',
                'internship_period_days',
            )
        }),
        ('Связанные документы и оборудование', {
            'fields': ('documents', 'equipment'),
            'description': '📄 Выберите документы и оборудование, относящиеся к данной должности',
            'classes': ('collapse',)
        }),
    )

    # Фильтры для боковой панели
    list_filter = ['organization', 'subdivision', 'department']
    # Очищаем стандартное отображение столбцов
    list_display = []
    search_fields = [
        'position_name',
        'safety_instructions_numbers'
    ]

    # Улучшенная система иконок для иерархии и профессий
    tree_settings = {
        'icons': {
            'organization': '🏢',
            'subdivision': '🏭',
            'department': '📂',
            'position': '👔',  # Базовая иконка для должности (будет заменена на специфичную)
            'employee': '👤',
            'no_subdivision': '🏗️',
            'no_department': '📁'
        },
        'fields': {
            'name_field': 'position_name',
            'organization_field': 'organization',
            'subdivision_field': 'subdivision',
            'department_field': 'department'
        },
        'display_rules': {
            'hide_empty_branches': False,
            'hide_no_subdivision_no_department': False
        }
    }

    # Добавляем инлайны для СИЗ и вредных факторов медосмотров
    inlines = [
        SIZNormInlineForPosition,
        PositionMedicalFactorInline,  # Инлайн для вредных факторов
    ]

    class Media:
        css = {
            'all': ('admin/css/widgets.css', 'admin/css/tree_view.css')
        }
        js = [
            'admin/js/jquery.init.js',
            'admin/js/core.js',
            'admin/js/SelectBox.js',
            'admin/js/SelectFilter2.js',
        ]

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Добавляем в контекст информацию о наличии медицинских факторов"""
        extra_context = extra_context or {}
        obj = self.get_object(request, object_id)
        if obj:
            extra_context['has_medical_factors'] = obj.medical_factors.exists()
        return super().change_view(request, object_id, form_url, extra_context)

    def get_urls(self):
        """🔗 Добавляем кастомные URL для подтягивания норм СИЗ и импорта/экспорта"""
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/copy_reference_norms/',
                self.admin_site.admin_view(self.copy_reference_norms_view),
                name='position_copy_reference_norms',
            ),
            path('import/', self.admin_site.admin_view(self.import_view), name='directory_position_import'),
            path('export/', self.admin_site.admin_view(self.export_view), name='directory_position_export'),
        ]
        return custom_urls + urls

    def copy_reference_norms_view(self, request, object_id):
        """👥 View для копирования эталонных норм в текущую должность

        Копирование выполняется только при точном совпадении названий должностей
        и только в исключительных случаях, когда в разных организациях
        для одинаковых профессий выдаются разные СИЗ.
        """
        position = self.get_object(request, object_id)
        if not position:
            messages.error(request, "Должность не найдена.")
            return redirect('admin:directory_position_change', object_id)

        # Находим эталонные нормы для этой должности
        reference_norms = Position.find_reference_norms(position.position_name)

        if not reference_norms.exists():
            messages.warning(request,
                             f"Эталонные нормы СИЗ для должности '{position.position_name}' не найдены. Проверьте, что существуют должности с точно таким же названием и у них есть нормы СИЗ.")
            return redirect('admin:directory_position_change', object_id)

        # Сначала удаляем все пустые нормы у этой должности
        SIZNorm.objects.filter(position=position, siz__isnull=True).delete()

        # Создаем набор для отслеживания уже добавленных норм
        added_norms = set()
        # Счетчики для статистики
        created_count = 0
        updated_count = 0
        errors_count = 0

        # Копируем нормы
        for norm in reference_norms:
            # Пропускаем нормы без указанного СИЗ
            if not norm.siz:
                continue

            # Создаем ключ на основе siz.id и condition
            norm_key = (norm.siz.id, norm.condition)

            # Проверяем, не добавляли ли уже такую норму
            if norm_key not in added_norms:
                try:
                    # Проверяем, существует ли уже такая норма
                    existing_norm = SIZNorm.objects.filter(
                        position=position,
                        siz=norm.siz,
                        condition=norm.condition
                    ).first()

                    if existing_norm:
                        # Обновляем существующую норму
                        existing_norm.quantity = norm.quantity
                        existing_norm.order = norm.order
                        existing_norm.save()
                        updated_count += 1
                    else:
                        # Создаем новую норму
                        SIZNorm.objects.create(
                            position=position,
                            siz=norm.siz,
                            quantity=norm.quantity,
                            condition=norm.condition,
                            order=norm.order
                        )
                        created_count += 1

                    # Добавляем ключ в набор добавленных норм
                    added_norms.add(norm_key)
                except Exception as e:
                    errors_count += 1
                    messages.error(
                        request,
                        f"Ошибка при копировании нормы для {norm.siz.name}: {str(e)}"
                    )

        # После копирования снова проверяем и удаляем все пустые нормы
        SIZNorm.objects.filter(position=position, siz__isnull=True).delete()

        if created_count > 0 or updated_count > 0:
            messages.success(
                request,
                f"Успешно применены эталонные нормы СИЗ: создано {created_count}, обновлено {updated_count}." +
                (f" Ошибок: {errors_count}." if errors_count > 0 else "")
            )
        else:
            messages.info(
                request,
                "Не было скопировано ни одной нормы СИЗ. Возможно, все нормы уже существуют или у этой должности уже есть все нормы." +
                (f" Ошибок: {errors_count}." if errors_count > 0 else "")
            )

        # После копирования и обработки всех норм, перенаправляем на страницу изменения должности
        return redirect('admin:directory_position_change', object_id)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """
        Настройка виджетов для полей many-to-many с FilteredSelectMultiple
        """
        if db_field.name == "documents":
            kwargs["widget"] = FilteredSelectMultiple(
                verbose_name="ДОСТУПНЫЕ ДОКУМЕНТЫ",
                is_stacked=False
            )
        if db_field.name == "equipment":
            kwargs["widget"] = FilteredSelectMultiple(
                verbose_name="ДОСТУПНОЕ ОБОРУДОВАНИЕ",
                is_stacked=False
            )
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def get_queryset(self, request):
        """
        🔒 Ограничиваем должности по организациям, доступным пользователю.
        Оптимизируем запрос подгрузкой связанных объектов.
        """
        qs = super().get_queryset(request).select_related(
            'organization',
            'subdivision',
            'department'
        ).prefetch_related(
            'documents',
            'equipment',
            'siz_norms',  # Предзагрузка СИЗ для оптимизации
            'medical_factors'  # Предзагрузка вредных факторов
        )
        if not request.user.is_superuser and hasattr(request.user, 'profile'):
            allowed_orgs = request.user.profile.organizations.all()
            qs = qs.filter(organization__in=allowed_orgs)
        return qs

    def get_form(self, request, obj=None, **kwargs):
        """
        🔑 Переопределяем get_form для:
        1) Передачи request.user в форму
        2) Фильтрации M2M-полей по организациям
        """
        Form = super().get_form(request, obj, **kwargs)

        class PositionFormWithUser(Form):
            def __init__(self, *args, **kwargs):
                self.user = request.user
                super().__init__(*args, **kwargs)
                # Настраиваем labels и help_text для полей
                self.fields['documents'].label = "ДОСТУПНЫЕ ДОКУМЕНТЫ"
                self.fields['equipment'].label = "ДОСТУПНОЕ ОБОРУДОВАНИЕ"
                self.fields[
                    'documents'].help_text = "Удерживайте 'Control' (или 'Command' на Mac), чтобы выбрать несколько значений."
                self.fields[
                    'equipment'].help_text = "Удерживайте 'Control' (или 'Command' на Mac), чтобы выбрать несколько значений."
                # Фильтруем документы и оборудование по организациям
                if hasattr(request.user, 'profile'):
                    allowed_orgs = request.user.profile.organizations.all()
                    # Базовые queryset
                    docs_qs = self.fields['documents'].queryset
                    equip_qs = self.fields['equipment'].queryset
                    # Если редактируем существующий объект
                    if obj:
                        # Фильтруем по организации объекта
                        docs_qs = docs_qs.filter(organization=obj.organization)
                        equip_qs = equip_qs.filter(organization=obj.organization)
                    # Фильтруем по доступным организациям
                    docs_qs = docs_qs.filter(organization__in=allowed_orgs).distinct().order_by('name')
                    equip_qs = equip_qs.filter(
                        organization__in=allowed_orgs).distinct().order_by('equipment_name')
                    self.fields['documents'].queryset = docs_qs
                    self.fields['equipment'].queryset = equip_qs

        return PositionFormWithUser

    def get_node_additional_data(self, obj):
        """
        Дополнительные данные для каждого узла в древовидном представлении.

        Проверяет наличие:
        1. Индикаторы СИЗ и медосмотров (сначала переопределения, затем эталонные)
        2. Роли в комиссиях (из таблицы CommissionMember)
        3. Прочие атрибуты должности
        """
        # Базовая информация
        profession_icon = get_profession_icon(obj.position_name)
        additional_data = {
            # Иконка профессии
            'profession_icon': profession_icon,

            # Основные атрибуты безопасности
            'is_responsible_for_safety': obj.is_responsible_for_safety,
            'can_be_internship_leader': obj.can_be_internship_leader,
            'can_sign_orders': obj.can_sign_orders,
            'is_electrical_personnel': obj.is_electrical_personnel,
            'electrical_group': obj.electrical_safety_group,
        }

        # ===== СИЗ =====
        # 1. Проверяем переопределенные нормы СИЗ
        has_custom_siz_norms = obj.siz_norms.exists()

        # 2. Если переопределений нет, проверяем эталонные нормы
        has_reference_siz_norms = False
        if not has_custom_siz_norms:
            has_reference_siz_norms = Position.find_reference_norms(obj.position_name).exists()

        # 3. Заполняем информацию о СИЗ
        additional_data['has_siz_norms'] = has_custom_siz_norms or has_reference_siz_norms
        if has_custom_siz_norms:
            additional_data['siz_norms_type'] = 'custom'
            additional_data['siz_norms_title'] = 'Переопределенные нормы СИЗ для данной должности'
        elif has_reference_siz_norms:
            additional_data['siz_norms_type'] = 'reference'
            additional_data['siz_norms_title'] = 'Используются стандартные нормы СИЗ'
        else:
            additional_data['siz_norms_type'] = 'none'
            additional_data['siz_norms_title'] = 'Нет норм СИЗ'

        # ===== МЕДОСМОТРЫ =====
        # 1. Проверяем переопределенные нормы медосмотров
        has_custom_medical_norms = obj.medical_factors.exists()

        # 2. Если переопределений нет, проверяем эталонные нормы
        has_reference_medical_norms = False
        if not has_custom_medical_norms:
            # Проверяем наличие эталонных норм медосмотров для этого типа должности
            has_reference_medical_norms = MedicalExaminationNorm.objects.filter(
                position_name=obj.position_name
            ).exists()

        # 3. Заполняем информацию о медосмотрах
        additional_data['has_medical_norms'] = has_custom_medical_norms or has_reference_medical_norms
        if has_custom_medical_norms:
            additional_data['medical_norms_type'] = 'custom'
            additional_data['medical_norms_title'] = 'Переопределенные нормы медосмотров для данной должности'
        elif has_reference_medical_norms:
            additional_data['medical_norms_type'] = 'reference'
            additional_data['medical_norms_title'] = 'Используются стандартные нормы медосмотров'
        else:
            additional_data['medical_norms_type'] = 'none'
            additional_data['medical_norms_title'] = 'Нет норм медосмотров'

        # ===== РОЛИ В КОМИССИЯХ =====
        # Получаем роли в комиссиях через CommissionMember
        # Находим всех сотрудников с этой должностью
        from directory.models import Employee
        employees_with_position = Employee.objects.filter(position=obj)

        # Находим все роли в комиссиях для этих сотрудников
        commission_roles = CommissionMember.objects.filter(
            employee__in=employees_with_position,
            is_active=True
        ).select_related('commission')

        # Группируем роли для отображения
        additional_data['commission_roles'] = []
        for role in commission_roles:
            additional_data['commission_roles'].append({
                'commission_name': role.commission.name,
                'role': role.role,
                'role_display': role.get_role_display(),
                'employee_name': role.employee.full_name_nominative
            })

        return additional_data

    def has_module_permission(self, request):
        """
        👮‍♂️ Проверка прав на доступ к модулю
        """
        if request.user.is_superuser:
            return True
        if hasattr(request.user, 'profile'):
            return request.user.profile.organizations.exists()
        return False

    def has_view_permission(self, request, obj=None):
        """
        👀 Проверка прав на просмотр
        """
        if request.user.is_superuser:
            return True
        if not obj:
            return True
        if hasattr(request.user, 'profile'):
            return obj.organization in request.user.profile.organizations.all()
        return False

    def has_change_permission(self, request, obj=None):
        """
        ✏️ Проверка прав на редактирование
        """
        return self.has_view_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        """
        🗑️ Проверка прав на удаление
        """
        return self.has_view_permission(request, obj)

    def import_view(self, request):
        """📥 Импорт организационной структуры"""
        context = self.admin_site.each_context(request)

        if request.method == 'POST':
            if 'confirm' in request.POST:
                # Финальное подтверждение импорта
                dataset_data = request.session.get('position_dataset')
                if not dataset_data:
                    messages.error(request, 'Данные для импорта не найдены. Загрузите файл заново.')
                    return redirect('admin:directory_position_import')

                dataset = Dataset().load(dataset_data)
                resource = OrganizationStructureResource()
                result = resource.import_data(dataset, dry_run=False)

                del request.session['position_dataset']

                messages.success(request, f'✅ Импорт завершен! Создано: {result.totals["new"]}, обновлено: {result.totals["update"]}')
                return redirect('admin:directory_position_changelist')
            else:
                # Предпросмотр импорта
                import_file = request.FILES.get('import_file')
                if not import_file:
                    messages.error(request, 'Файл не выбран')
                    return redirect('admin:directory_position_import')

                file_format = import_file.name.split('.')[-1].lower()
                if file_format not in ['xlsx', 'xls']:
                    messages.error(request, 'Поддерживаются только файлы XLSX и XLS')
                    return redirect('admin:directory_position_import')

                try:
                    dataset = Dataset().load(import_file.read(), format=file_format)
                    resource = OrganizationStructureResource()
                    result = resource.import_data(dataset, dry_run=True)

                    # Сохраняем данные в сессии для финального импорта
                    request.session['position_dataset'] = dataset.export('json')

                    context.update({
                        'title': 'Предпросмотр импорта организационной структуры',
                        'result': result,
                        'dataset': dataset,
                    })
                    return render(request, 'admin/directory/position/import_preview.html', context)
                except Exception as e:
                    messages.error(request, f'Ошибка при обработке файла: {str(e)}')
                    return redirect('admin:directory_position_import')

        context.update({
            'title': 'Импорт организационной структуры',
            'subtitle': None,
        })
        return render(request, 'admin/directory/position/import.html', context)

    def export_view(self, request):
        """📤 Экспорт организационной структуры"""
        from directory.models import Organization

        # Фильтрация по организации (если указана)
        organization_id = request.GET.get('organization_id')

        if organization_id:
            queryset = Position.objects.filter(organization_id=organization_id)
        else:
            queryset = Position.objects.all()

        # Применяем права доступа
        if not request.user.is_superuser and hasattr(request.user, 'profile'):
            allowed_orgs = request.user.profile.organizations.all()
            queryset = queryset.filter(organization__in=allowed_orgs)

        queryset = queryset.select_related('organization', 'subdivision', 'department')

        resource = OrganizationStructureResource()
        dataset = resource.export(queryset)

        response = HttpResponse(
            dataset.export('xlsx'),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="organization_structure.xlsx"'
        return response