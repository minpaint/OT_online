from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils.html import format_html
from directory.models.profile import Profile
from directory.utils.permissions import AccessControlHelper
# Импортируем нашу кастомную форму
from directory.admin.profile import ProfileAdminForm


class ProfileInline(admin.StackedInline):
    """
    👤 Inline для редактирования профиля пользователя с иерархическим доступом.

    Позволяет назначать права доступа на трёх уровнях:
    - 🏢 Organizations - доступ ко ВСЕЙ организации
    - 🏭 Subdivisions - доступ к подразделениям (включая их отделы)
    - 📂 Departments - доступ только к конкретным отделам
    """
    model = Profile
    form = ProfileAdminForm  # Используем кастомную форму с карточным виджетом
    can_delete = False
    verbose_name_plural = 'Профиль и права доступа'

    fieldsets = (
        ('Основные настройки', {
            'fields': ('is_active',)
        }),
        ('Права доступа', {
            'fields': ('hierarchical_access',),
            'description': format_html(
                '<div style="background: #f8f8f8; border: 1px solid #ccc; '
                'padding: 12px; border-radius: 4px; margin-bottom: 10px; color: #333; font-size: 13px;">'
                '<strong>Иерархический принцип доступа:</strong><br>'
                '<ul style="margin: 8px 0; padding-left: 20px; line-height: 1.6;">'
                '<li><strong>🏢 Организация</strong> — полный доступ ко всей организации (все подразделения и отделы)</li>'
                '<li><strong>🏭 Подразделение</strong> — доступ к подразделению и всем его отделам</li>'
                '<li><strong>📂 Отдел</strong> — доступ только к конкретному отделу</li>'
                '</ul>'
                '<em style="color: #666;">Выберите галочками нужные уровни. Карточки разворачиваются кликом на заголовок.</em>'
                '</div>'
            )
        }),
        ('🍔 Управление меню', {
            'fields': ('visible_menu_items',),
            'description': format_html(
                '<div style="background: #f0f8ff; border: 1px solid #b0d4f1; '
                'padding: 12px; border-radius: 4px; margin-bottom: 10px; color: #333; font-size: 13px;">'
                '<strong>Настройка видимых пунктов меню:</strong><br>'
                '<p style="margin: 8px 0; line-height: 1.6;">'
                'Выберите пункты меню, которые будут доступны пользователю в боковой и верхней навигации. '
                '<strong>Если ничего не выбрано</strong> — пользователь видит все активные пункты меню.'
                '</p>'
                '<em style="color: #666;">Используйте двойные списки для перемещения пунктов. '
                'Применяется только к неадминским пользователям.</em>'
                '</div>'
            ),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['get_access_level_display', 'get_redundancy_warning']

    def get_access_level_display(self, obj):
        """Отображает уровень доступа пользователя"""
        if not obj or not obj.pk:
            return '-'

        level = AccessControlHelper.get_user_access_level(obj.user)

        icons = {
            'superuser': '👑 Суперпользователь (полный доступ)',
            'organization': '🏢 Уровень организации',
            'subdivision': '🏭 Уровень подразделения',
            'department': '📂 Уровень отдела',
            'none': '❌ Нет прав доступа'
        }

        return format_html(
            '<span style="font-size: 14px; font-weight: bold;">{}</span>',
            icons.get(level, level)
        )

    get_access_level_display.short_description = 'Текущий уровень доступа'

    def get_redundancy_warning(self, obj):
        """Показывает предупреждение об избыточных правах"""
        if not obj or not obj.pk:
            return '-'

        redundant = obj.check_redundant_access()

        if not redundant:
            return format_html(
                '<span style="color: green;">✅ Избыточных прав не обнаружено</span>'
            )

        html = '<div style="background: #fff3cd; border: 1px solid #ffc107; padding: 10px; border-radius: 4px;">'
        html += '<strong style="color: #856404;">⚠️ Обнаружены избыточные права:</strong><ul style="margin: 10px 0;">'

        for item in redundant:
            html += f'<li style="color: #856404;">{item}</li>'

        html += '</ul></div>'

        return format_html(html)

    get_redundancy_warning.short_description = 'Проверка избыточности'

    def get_fieldsets(self, request, obj=None):
        """Динамически добавляем поля для отображения информации"""
        fieldsets = super().get_fieldsets(request, obj)

        if obj and obj.pk:
            # Добавляем информационную секцию
            info_fieldset = (
                'Информация о правах доступа', {
                    'fields': ('get_access_level_display', 'get_redundancy_warning'),
                    'classes': ('collapse',)
                }
            )
            fieldsets = fieldsets + (info_fieldset,)

        return fieldsets


class CustomUserAdmin(UserAdmin):
    """
    ⚙️ Кастомный UserAdmin с расширенным профилем и проверкой прав доступа.
    """
    inlines = (ProfileInline,)

    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_access_level')

    def get_access_level(self, obj):
        """Отображает уровень доступа в списке пользователей"""
        if obj.is_superuser:
            return '👑 Супер'

        if not hasattr(obj, 'profile'):
            return '❌ Нет профиля'

        level = AccessControlHelper.get_user_access_level(obj)

        icons = {
            'organization': '🏢 Орг',
            'subdivision': '🏭 Подр',
            'department': '📂 Отд',
            'none': '❌ Нет'
        }

        return icons.get(level, level)

    get_access_level.short_description = 'Уровень доступа'

    def save_related(self, request, form, formsets, change):
        """
        Переопределяем save_related для проверки избыточных прав после сохранения M2M.
        """
        super().save_related(request, form, formsets, change)

        # Проверяем избыточность прав для профиля
        user = form.instance
        if hasattr(user, 'profile'):
            redundant = user.profile.check_redundant_access()

            if redundant:
                messages.warning(
                    request,
                    format_html(
                        '<strong>⚠️ Обнаружены избыточные права доступа:</strong><br>'
                        '<ul>{}</ul>',
                        format_html(''.join(f'<li>{item}</li>' for item in redundant))
                    )
                )


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
