from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    """
    👤 Профиль пользователя с доступом к организациям
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name="Пользователь"
    )
    organizations = models.ManyToManyField(
        'directory.Organization',
        verbose_name="Организации",
        related_name="user_profiles",
        help_text="🏢 Организации, к которым у пользователя есть доступ"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"

    def __str__(self):
        return f"Профиль пользователя {self.user.username}"

    def get_organizations_display(self):
        """
        🔍 Возвращает список организаций в виде строки (пример: "Орг1, Орг2").
        """
        return ", ".join(org.short_name_ru for org in self.organizations.all())
