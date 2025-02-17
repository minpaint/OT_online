from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from directory.models.profile import Profile

class ProfileInline(admin.StackedInline):
    """
    👤 Inline для редактирования профиля пользователя.
    Позволяет редактировать поле organizations (с filter_horizontal) непосредственно
    при редактировании пользователя.
    """
    model = Profile
    can_delete = False
    verbose_name_plural = 'Профиль пользователя'
    filter_horizontal = ('organizations',)
    fieldsets = (
        (None, {'fields': ('organizations', 'is_active')}),
    )

class CustomUserAdmin(UserAdmin):
    """
    ⚙️ Кастомный UserAdmin с добавлением инлайна ProfileInline.
    """
    inlines = (ProfileInline, )

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
