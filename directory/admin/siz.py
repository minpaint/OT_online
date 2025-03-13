from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from directory.models.siz import SIZ, SIZNorm
from directory.models.position import Position
from directory.forms.siz import SIZForm, SIZNormForm
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from django.db.models import Count, Case, When, Value, IntegerField, Q
from django.utils.translation import ngettext
from django.contrib import messages
from django.db.models.functions import Lower


class SIZResource(resources.ModelResource):
    """🔄 Ресурс для импорта/экспорта данных СИЗ"""

    class Meta:
        model = SIZ
        fields = ('name', 'classification', 'unit', 'wear_period')
        export_order = ('name', 'classification', 'unit', 'wear_period')
        import_id_fields = []  # Пустой список означает "всегда создавать новые записи"


@admin.register(SIZ)
class SIZAdmin(ImportExportModelAdmin):
    """🛡️ Административный интерфейс для СИЗ"""
    resource_class = SIZResource
    form = SIZForm
    list_display = ('name', 'classification', 'unit', 'get_wear_period', 'norms_count')
    list_filter = ('classification', 'unit')
    search_fields = ('name', 'classification')
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'classification', 'unit', 'wear_period')
        }),
    )

    def get_wear_period(self, obj):
        """🕒 Получение отображаемого значения срока носки"""
        return "До износа" if obj.wear_period == 0 else f"{obj.wear_period} мес."

    get_wear_period.short_description = "Срок носки"

    def norms_count(self, obj):
        """🔢 Количество норм, где используется данное СИЗ"""
        count = obj.norms.count()
        if count > 0:
            url = reverse('admin:directory_siznorm_changelist') + f'?siz__id__exact={obj.id}'
            return format_html('<a href="{}">{} норм</a>', url, count)
        return "0 норм"

    norms_count.short_description = "Использование"


class SIZNormInline(admin.TabularInline):
    """📋 Встроенный интерфейс для норм выдачи СИЗ"""
    model = SIZNorm
    extra = 1
    fields = ('siz', 'classification_display', 'unit_display', 'quantity', 'condition', 'wear_period_display')
    readonly_fields = ('classification_display', 'unit_display', 'wear_period_display')
    autocomplete_fields = ['siz']

    def classification_display(self, obj):
        """🏷️ Отображение классификации СИЗ"""
        return obj.siz.classification if obj.siz else '-'

    classification_display.short_description = "Классификация"

    def unit_display(self, obj):
        """📏 Отображение единицы измерения СИЗ"""
        return obj.siz.unit if obj.siz else '-'

    unit_display.short_description = "Единица измерения"

    def wear_period_display(self, obj):
        """🕒 Отображение срока носки СИЗ"""
        if not obj.siz:
            return '-'
        return "До износа" if obj.siz.wear_period == 0 else f"{obj.siz.wear_period} мес."

    wear_period_display.short_description = "Срок носки"


class SIZNormInlineForPosition(admin.TabularInline):
    """📋 Встроенные нормы СИЗ для должности с группировкой по условиям"""
    model = SIZNorm
    extra = 1
    fields = ('siz', 'quantity', 'condition', 'order')
    verbose_name = "Норма СИЗ"
    verbose_name_plural = "Нормы СИЗ"
    autocomplete_fields = ['siz']

    def get_queryset(self, request):
        """🔍 Оптимизация запроса для получения всех норм для должности"""
        return super().get_queryset(request)


@admin.register(SIZNorm)
class SIZNormAdmin(admin.ModelAdmin):
    """📊 Административный интерфейс для норм выдачи СИЗ"""
    form = SIZNormForm
    list_display = ('position', 'siz', 'quantity', 'get_condition', 'order')
    list_filter = ('position', 'condition', 'siz')
    search_fields = ('position__position_name', 'siz__name', 'condition')
    autocomplete_fields = ['siz']
    # Указываем шаблон для отображения древовидной структуры
    change_list_template = "admin/directory/siznorm/change_list_tree.html"

    fieldsets = (
        ('Основная информация', {
            'fields': ('unique_position_name', 'siz', 'quantity', 'order')
        }),
        ('Условия выдачи', {
            'fields': ('condition',),
            'description': 'Укажите условие выдачи СИЗ (например, "При работе в зимнее время", "При влажной уборке" и т.д.)'
        }),
    )

    def get_condition(self, obj):
        """📝 Получение условия выдачи для отображения в списке"""
        return obj.condition if obj.condition else "Основная норма"

    get_condition.short_description = "Условие выдачи"

    def get_form(self, request, obj=None, **kwargs):
        """Получение формы с передачей дополнительных параметров"""
        position_id = request.GET.get('position')
        Form = super().get_form(request, obj, **kwargs)

        if position_id:
            # Создаем замыкание с position_id
            class FormWithPosition(Form):
                def __new__(cls, *args, **kwargs):
                    kwargs['position_id'] = position_id
                    return Form(*args, **kwargs)

            return FormWithPosition
        return Form

    def changelist_view(self, request, extra_context=None):
        """
        📋 Представление списка норм СИЗ с группировкой по профессиям и условиям

        Формирует структуру данных для шаблона, где нормы СИЗ группируются:
        1. По названиям профессий/должностей
        2. По условиям выдачи СИЗ внутри каждой профессии
        """
        extra_context = extra_context or {}

        # Получаем уникальные названия профессий, у которых есть нормы СИЗ
        position_names = Position.objects.filter(
            siz_norms__isnull=False
        ).values_list('position_name', flat=True).distinct().order_by(Lower('position_name'))

        # Данные профессий
        professions_data = []

        for position_name in position_names:
            # Получаем все должности с таким названием
            positions = Position.objects.filter(position_name=position_name)

            # Берем первую должность как эталонную (по алфавиту организаций)
            reference_position = positions.order_by('organization__full_name_ru').first()

            if not reference_position:
                continue

            # Получаем все нормы СИЗ для эталонной должности
            all_norms = SIZNorm.objects.filter(position=reference_position).select_related('siz', 'position')

            # Базовые нормы (без условий)
            base_norms = all_norms.filter(condition='').order_by('order', 'siz__name')

            # 🔄 ИСПРАВЛЕНИЕ: Получаем уникальные условия и группируем нормы более эффективно
            # Используем словарь для хранения сгруппированных норм, чтобы избежать дублирования
            grouped_norms = {}

            # Выбираем только нормы с условиями
            condition_norms = all_norms.exclude(condition='')

            # Группируем нормы по названию условия
            for norm in condition_norms:
                condition_name = norm.condition

                # Инициализируем список для условия, если он еще не существует
                if condition_name not in grouped_norms:
                    grouped_norms[condition_name] = []

                # Добавляем норму в группу, избегая дублирования
                # Проверяем, нет ли уже такой комбинации СИЗ+условие
                norm_key = f"{norm.siz_id}_{norm.condition}"
                exists = False
                for existing_norm in grouped_norms[condition_name]:
                    existing_key = f"{existing_norm.siz_id}_{existing_norm.condition}"
                    if existing_key == norm_key:
                        exists = True
                        break

                if not exists:
                    grouped_norms[condition_name].append(norm)

            # Преобразуем словарь в список для шаблона
            group_norms = []
            for condition_name, norms in grouped_norms.items():
                # Сортируем нормы по порядку
                sorted_norms = sorted(norms, key=lambda x: (x.order, x.siz.name))
                group_norms.append({
                    'name': condition_name,
                    'norms': sorted_norms
                })

            # Добавляем информацию о профессии
            profession_data = {
                'name': position_name,
                'positions': positions,
                'base_norms': base_norms,
                'group_norms': group_norms,
            }

            professions_data.append(profession_data)

        extra_context['professions'] = professions_data

        return super().changelist_view(request, extra_context)