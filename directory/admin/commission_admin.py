# directory/admin/commission_admin.py

from django.contrib import admin
from django.utils.html import format_html
from directory.models import Commission, CommissionMember


class CommissionMemberInline(admin.TabularInline):
    """Встроенная админка для участников комиссии"""
    model = CommissionMember
    extra = 1
    autocomplete_fields = ['employee']
    fields = ['employee', 'role', 'is_active']


@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    """Административный интерфейс для комиссий"""
    list_display = ['name', 'commission_type_display', 'level_display', 'members_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'commission_type', 'created_at']
    search_fields = ['name']
    inlines = [CommissionMemberInline]

    fieldsets = [
        (None, {'fields': ['name', 'commission_type', 'is_active']}),
        ('Привязка к структуре', {'fields': ['organization', 'subdivision', 'department']}),
    ]

    def commission_type_display(self, obj):
        """Отображает тип комиссии с иконкой"""
        icons = {
            'ot': '🛡️',
            'eb': '⚡',
            'pb': '🔥',
            'other': '📋'
        }
        icon = icons.get(obj.commission_type, '📋')
        return format_html('{} {}', icon, obj.get_commission_type_display())

    commission_type_display.short_description = 'Тип комиссии'

    def level_display(self, obj):
        """Отображает уровень комиссии"""
        return obj.get_level_display()

    level_display.short_description = 'Уровень'

    def members_count(self, obj):
        """Отображает количество активных участников комиссии"""
        count = obj.members.filter(is_active=True).count()
        return count

    members_count.short_description = 'Участников'


@admin.register(CommissionMember)
class CommissionMemberAdmin(admin.ModelAdmin):
    """Административный интерфейс для участников комиссии"""
    list_display = ['employee', 'role_display', 'commission', 'is_active']
    list_filter = ['is_active', 'role', 'commission']
    search_fields = ['employee__full_name_nominative', 'commission__name']
    autocomplete_fields = ['employee', 'commission']

    def role_display(self, obj):
        """Отображает роль участника с иконкой"""
        icons = {
            'chairman': '👑',
            'member': '👤',
            'secretary': '📝'
        }
        icon = icons.get(obj.role, '👤')
        return format_html('{} {}', icon, obj.get_role_display())

    role_display.short_description = 'Роль'