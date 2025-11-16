# deadline_control/admin/key_deadline.py
from django.contrib import admin
from django.utils.html import format_html
from deadline_control.models import KeyDeadlineCategory, KeyDeadlineItem


class KeyDeadlineItemInline(admin.TabularInline):
    """
    Инлайн для мероприятий в категории ключевых сроков
    """
    model = KeyDeadlineItem
    extra = 1
    fields = [
        'name', 'periodicity_months', 'current_date',
        'next_date_display', 'days_display', 'responsible_person', 'notes'
    ]
    readonly_fields = ['next_date_display', 'days_display']

    def next_date_display(self, obj):
        """Отображение следующей даты с цветовой индикацией"""
        if not obj.next_date:
            return '-'

        days = obj.days_until_next()
        if days is None:
            return format_html('<span>{}</span>', obj.next_date)

        if days < 0:
            # Просрочено - красный
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠️ {} (просрочено {} дн.)</span>',
                obj.next_date, abs(days)
            )
        elif days <= 14:
            # Скоро - оранжевый
            return format_html(
                '<span style="color: orange; font-weight: bold;">⏰ {} (осталось {} дн.)</span>',
                obj.next_date, days
            )
        else:
            # Норма - зелёный
            return format_html(
                '<span style="color: green;">✅ {} (через {} дн.)</span>',
                obj.next_date, days
            )
    next_date_display.short_description = "Дата следующего проведения"

    def days_display(self, obj):
        """Отображение количества дней до следующего проведения"""
        days = obj.days_until_next()
        if days is None:
            return '-'

        if days < 0:
            return format_html('<span style="color: red;">Просрочено на {} дн.</span>', abs(days))
        elif days <= 14:
            return format_html('<span style="color: orange;">Осталось {} дн.</span>', days)
        else:
            return format_html('<span style="color: green;">Через {} дн.</span>', days)
    days_display.short_description = "Статус"


@admin.register(KeyDeadlineCategory)
class KeyDeadlineCategoryAdmin(admin.ModelAdmin):
    """
    Админ-панель для категорий ключевых сроков
    """
    list_display = ['name', 'organization', 'items_count', 'overdue_count', 'is_active']
    list_filter = ['organization', 'is_active']
    search_fields = ['name', 'description']
    inlines = [KeyDeadlineItemInline]

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'organization', 'is_active')
        }),
        ('Дополнительно', {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
    )

    def items_count(self, obj):
        """Количество мероприятий в категории"""
        count = obj.items.count()
        return format_html('<span>{}</span>', count)
    items_count.short_description = "Мероприятий"

    def overdue_count(self, obj):
        """Количество просроченных мероприятий"""
        overdue = sum(1 for item in obj.items.all() if item.is_overdue())
        if overdue > 0:
            return format_html('<span style="color: red; font-weight: bold;">⚠️ {}</span>', overdue)
        return format_html('<span style="color: green;">✅ 0</span>')
    overdue_count.short_description = "Просрочено"

    def get_queryset(self, request):
        """Фильтрация по организациям пользователя"""
        qs = super().get_queryset(request)
        if not request.user.is_superuser and hasattr(request.user, 'profile'):
            allowed_orgs = request.user.profile.organizations.all()
            qs = qs.filter(organization__in=allowed_orgs)
        return qs.prefetch_related('items')
