# directory/admin/menu_item.py
"""
Admin интерфейс для управления пунктами меню системы.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from directory.models import MenuItem


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    """
    🍔 Администрирование пунктов меню

    Иерархическое отображение с возможностью управления структурой меню.
    """

    list_display = [
        'icon_display',
        'name_hierarchy',
        'url_display',
        'location_badge',
        'order',
        'is_active_badge',
        'has_children_badge'
    ]

    list_filter = ['location', 'is_active', 'requires_auth', 'parent']

    search_fields = ['name', 'url_name', 'url', 'description']

    fieldsets = (
        ('📋 Основная информация', {
            'fields': ('name', 'icon', 'parent', 'order')
        }),
        ('🔗 URL конфигурация', {
            'fields': ('url_name', 'url'),
            'description': 'Укажите либо URL name (приоритет), либо прямой URL'
        }),
        ('⚙️ Настройки отображения', {
            'fields': ('location', 'is_active', 'requires_auth', 'is_separator')
        }),
        ('📝 Дополнительно', {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
    )

    ordering = ['parent__order', 'parent__name', 'order', 'name']

    def icon_display(self, obj):
        """Отображение иконки"""
        if obj.icon:
            return format_html('<span style="font-size: 18px;">{}</span>', obj.icon)
        return '—'
    icon_display.short_description = '🎨'

    def name_hierarchy(self, obj):
        """Отображение названия с учетом иерархии"""
        if obj.parent:
            indent = '&nbsp;&nbsp;&nbsp;&nbsp;' * self._get_level(obj)
            return format_html(
                '{}<span style="color: #999;">└─</span> {}',
                format_html(indent),
                obj.name
            )
        return format_html('<strong>{}</strong>', obj.name)
    name_hierarchy.short_description = 'Название'

    def _get_level(self, obj, level=0):
        """Рекурсивное определение уровня вложенности"""
        if obj.parent:
            return self._get_level(obj.parent, level + 1)
        return level

    def url_display(self, obj):
        """Отображение URL"""
        url = obj.get_url()
        if url and url != '#':
            return format_html(
                '<a href="{}" target="_blank" style="color: #447e9b;">{}</a>',
                url,
                obj.url_name or url[:50]
            )
        return format_html('<span style="color: #999;">{}</span>', obj.url_name or '—')
    url_display.short_description = 'URL'

    def location_badge(self, obj):
        """Отображение расположения в виде бейджа"""
        colors = {
            'sidebar': '#417690',
            'top': '#5b80b2',
            'both': '#205067'
        }
        labels = {
            'sidebar': 'Боковое',
            'top': 'Верхнее',
            'both': 'Оба'
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            colors.get(obj.location, '#999'),
            labels.get(obj.location, obj.location)
        )
    location_badge.short_description = 'Расположение'

    def is_active_badge(self, obj):
        """Отображение статуса активности"""
        if obj.is_active:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">✓ Активен</span>'
            )
        return format_html(
            '<span style="color: #dc3545; font-weight: bold;">✗ Неактивен</span>'
        )
    is_active_badge.short_description = 'Статус'

    def has_children_badge(self, obj):
        """Отображение наличия дочерних элементов"""
        if obj.has_children():
            count = obj.children.count()
            return format_html(
                '<span style="color: #666;">📁 {}</span>',
                count
            )
        return format_html('<span style="color: #ccc;">📄</span>')
    has_children_badge.short_description = 'Вложенные'

    def get_queryset(self, request):
        """Оптимизация запросов"""
        qs = super().get_queryset(request)
        return qs.select_related('parent').prefetch_related('children')

    class Media:
        css = {
            'all': ('admin/css/menu_item_admin.css',)
        }
