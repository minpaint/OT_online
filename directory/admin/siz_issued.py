# 📁 directory/admin/siz_issued.py
from django.contrib import admin
from django.utils.html import format_html
from directory.models.siz_issued import SIZIssued


@admin.register(SIZIssued)
class SIZIssuedAdmin(admin.ModelAdmin):
    """
    🛡️ Административный интерфейс для выданных СИЗ
    """
    list_display = ('employee', 'siz', 'issue_date', 'quantity', 'status_color', 'is_returned', 'return_date')
    list_filter = ('issue_date', 'is_returned', 'employee__organization', 'employee__subdivision')
    search_fields = ('employee__full_name_nominative', 'siz__name', 'notes', 'condition')
    date_hierarchy = 'issue_date'

    fieldsets = (
        ('Основная информация', {
            'fields': ('employee', 'siz', 'issue_date', 'quantity', 'condition')
        }),
        ('Состояние', {
            'fields': ('is_returned', 'return_date', 'wear_percentage', 'replacement_date')
        }),
        ('Дополнительно', {
            'fields': ('cost', 'notes', 'received_signature')
        }),
    )

    def status_color(self, obj):
        """
        🎨 Возвращает статус выданного СИЗ с цветовой индикацией
        """
        status = obj.status

        if obj.is_returned:
            color = "#6c757d"  # Серый
            return format_html('<span style="color: {};">⬅️ {}</span>', color, status)

        days = obj.days_until_replacement
        wear = obj.wear_percentage

        if days is not None and days <= 0:
            color = "#dc3545"  # Красный
            return format_html('<span style="color: {};">⚠️ {}</span>', color, status)

        if wear >= 80:
            color = "#dc3545"  # Красный
            return format_html('<span style="color: {};">🔴 {}</span>', color, status)
        elif wear >= 50:
            color = "#ffc107"  # Желтый
            return format_html('<span style="color: {};">🟡 {}</span>', color, status)
        else:
            color = "#28a745"  # Зеленый
            return format_html('<span style="color: {};">🟢 {}</span>', color, status)

    status_color.short_description = "Статус"

    def get_queryset(self, request):
        """
        🔒 Ограничиваем список выданных СИЗ по организациям пользователя
        """
        qs = super().get_queryset(request)
        if not request.user.is_superuser and hasattr(request.user, 'profile'):
            allowed_orgs = request.user.profile.organizations.all()
            qs = qs.filter(employee__organization__in=allowed_orgs)
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        🔍 Ограничиваем выбор связанных полей по организациям пользователя
        """
        if db_field.name == "employee" and not request.user.is_superuser and hasattr(request.user, 'profile'):
            allowed_orgs = request.user.profile.organizations.all()
            kwargs["queryset"] = db_field.related_model.objects.filter(
                organization__in=allowed_orgs
            ).order_by('full_name_nominative')

        return super().formfield_for_foreignkey(db_field, request, **kwargs)