# D:\YandexDisk\OT_online\directory\admin\position.py
"""
👔 Админ-класс для модели Position с древовидным отображением.
Используем кастомный шаблон для вывода change list в виде таблицы.
Логика ограничения по организациям (если не суперпользователь) сохраняется.
"""

from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.translation import ngettext
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import path, reverse
from directory.models import Position
from directory.forms.position import PositionForm
from directory.admin.mixins.tree_view import TreeViewMixin
from directory.models.siz import SIZNorm, SIZ
from directory.models.medical_norm import PositionMedicalFactor
from directory.models.medical_examination import HarmfulFactor


# Обновленный инлайн для СИЗ
class SIZNormInlineForPosition(admin.TabularInline):
    """📋 Встроенные нормы СИЗ для должности с отображением всех полей"""
    model = SIZNorm
    extra = 0  # Изменено с 1 на 0, чтобы не добавлять пустую строку автоматически
    fields = ('siz', 'classification', 'unit', 'quantity', 'wear_period', 'condition', 'order')
    readonly_fields = ('classification', 'unit', 'wear_period')
    verbose_name = "Норма СИЗ"
    verbose_name_plural = "Нормы СИЗ"
    autocomplete_fields = ['siz']

    # Предотвращаем отображение пустых форм
    def get_extra(self, request, obj=None, **kwargs):
        """Возвращает 0 для существующих объектов, 1 для новых"""
        return 0 if obj else 1

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
        return form_field


# Новый инлайн для вредных факторов медосмотров
class PositionMedicalFactorInline(admin.TabularInline):
    """🏥 Встроенные вредные факторы для должности"""
    model = PositionMedicalFactor
    extra = 0
    fields = ('harmful_factor', 'examination_type', 'periodicity', 'periodicity_override', 'is_disabled', 'notes')
    readonly_fields = ('examination_type', 'periodicity')
    verbose_name = "Вредный фактор медосмотра"
    verbose_name_plural = "Вредные факторы медосмотров"
    autocomplete_fields = ['harmful_factor']

    def get_extra(self, request, obj=None, **kwargs):
        """Возвращает 0 для существующих объектов, 1 для новых"""
        return 0 if obj else 1

    def get_queryset(self, request):
        """Оптимизированный запрос"""
        return super().get_queryset(request).select_related(
            'harmful_factor', 'harmful_factor__examination_type'
        ).filter(
            harmful_factor__isnull=False
        ).order_by('harmful_factor__short_name')

    def examination_type(self, obj):
        """🏥 Отображение типа медосмотра"""
        return obj.harmful_factor.examination_type.name if obj.harmful_factor and obj.harmful_factor.examination_type else ""

    examination_type.short_description = "Вид медосмотра"

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
        if db_field.name == 'notes':
            form_field.widget.attrs['style'] = 'width: 200px;'
        return form_field


@admin.register(Position)
class PositionAdmin(TreeViewMixin, admin.ModelAdmin):
    form = PositionForm
    # Указываем путь к шаблону для древовидного отображения
    change_list_template = "admin/directory/position/change_list_tree.html"
    # Указываем кастомный шаблон формы для добавления кнопки подтягивания норм
    change_form_template = "admin/directory/position/change_form.html"

    # Определяем порядок полей в форме
    fieldsets = (
        ('Основная информация', {
            'fields': (
                'position_name',
                'organization',
                'subdivision',
                'department',
                'commission_role',
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
        PositionMedicalFactorInline,  # Добавляем инлайн для вредных факторов
    ]

    class Media:
        css = {
            'all': ('admin/css/widgets.css', 'admin/css/position_siz_norms.css',)
        }
        js = [
            'admin/js/jquery.init.js',
            'admin/js/core.js',
            'admin/js/SelectBox.js',
            'admin/js/SelectFilter2.js',
            'admin/js/position_siz_norms.js',  # JS файл для управления нормами СИЗ
        ]

    def get_profession_icon(self, position_name):
        """
        Определяет эмоджи для профессии на основе её названия
        Аналогично методу в MedicalExaminationNormAdmin
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

    def get_urls(self):
        """🔗 Добавляем кастомный URL для подтягивания норм СИЗ"""
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/copy_reference_norms/',
                self.admin_site.admin_view(self.copy_reference_norms_view),
                name='position_copy_reference_norms',
            ),
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
        """
        qs = super().get_queryset(request).select_related(
            'organization',
            'subdivision',
            'department'
        ).prefetch_related(
            'documents',
            'equipment',
            'siz_norms',  # Добавляем предзагрузку СИЗ для оптимизации
            'medical_factors'  # Добавляем предзагрузку вредных факторов
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

    def get_additional_node_data(self, obj):
        """
        ➕ Добавляем иконку профессии, определенную на основе названия
        """
        # Определяем иконку профессии на основе названия
        profession_icon = self.get_profession_icon(obj.position_name)

        # Проверяем наличие эталонных норм
        has_reference_norms = Position.find_reference_norms(obj.position_name).exists()

        # Подсчитываем количество норм, но не разделяем по условиям
        total_norms_count = obj.siz_norms.count()

        # Подсчитываем количество вредных факторов для медосмотров
        medical_factors_count = obj.medical_factors.count()

        return {
            # Иконка профессии (новое!)
            'profession_icon': profession_icon,

            # Основные атрибуты безопасности
            'is_responsible_for_safety': obj.is_responsible_for_safety,
            'can_be_internship_leader': obj.can_be_internship_leader,
            'is_electrical_personnel': obj.is_electrical_personnel,

            # Счетчики связанных объектов
            'documents_count': obj.documents.count(),
            'equipment_count': obj.equipment.count(),

            # Упрощенная информация о СИЗ
            'total_siz_norms': total_norms_count,
            'has_reference_norms': has_reference_norms,

            # Информация о медосмотрах
            'medical_factors_count': medical_factors_count,
        }

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