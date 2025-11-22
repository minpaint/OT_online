from django.db import models
from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)


class Profile(models.Model):
    """
    👤 Профиль пользователя с иерархическим доступом (Scope-Based Access Control)

    Уровни доступа (по приоритету):
    1. 🏢 Organizations - доступ ко ВСЕЙ организации (все подразделения и отделы)
    2. 🏭 Subdivisions - доступ к подразделениям (включая их отделы)
    3. 📂 Departments - доступ только к конкретным отделам
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name="Пользователь"
    )

    # Иерархический доступ (Scope-Based)
    organizations = models.ManyToManyField(
        'directory.Organization',
        blank=True,
        verbose_name="Организации",
        related_name="user_profiles",
        help_text="🏢 Доступ ко ВСЕЙ организации (все подразделения и отделы)"
    )
    subdivisions = models.ManyToManyField(
        'directory.StructuralSubdivision',
        blank=True,
        verbose_name="Структурные подразделения",
        related_name="user_profiles",
        help_text="🏭 Доступ к подразделениям (включая их отделы)"
    )
    departments = models.ManyToManyField(
        'directory.Department',
        blank=True,
        verbose_name="Отделы",
        related_name="user_profiles",
        help_text="📂 Доступ только к конкретным отделам"
    )

    # Управление доступом к меню
    visible_menu_items = models.ManyToManyField(
        'directory.MenuItem',
        blank=True,
        verbose_name="Доступные пункты меню",
        related_name="user_profiles",
        help_text="🍔 Пункты меню, доступные пользователю. Если не указаны - доступны все."
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

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # После сохранения M2M проверяем избыточность прав
        # Вызывается через signal, т.к. M2M сохраняются после save()

    def check_redundant_access(self):
        """
        Проверяет избыточные права и логирует предупреждения.
        Не блокирует сохранение, но выводит warning в лог.

        Избыточность:
        - Подразделение, если уже дан доступ к его организации
        - Отдел, если уже дан доступ к его организации или подразделению
        """
        redundant = []

        # Проверяем subdivisions
        for subdiv in self.subdivisions.all():
            if subdiv.organization in self.organizations.all():
                redundant.append(
                    f"Подразделение '{subdiv.name}' избыточно - "
                    f"уже дан доступ к организации '{subdiv.organization}'"
                )

        # Проверяем departments
        for dept in self.departments.all():
            if dept.organization in self.organizations.all():
                redundant.append(
                    f"Отдел '{dept.name}' избыточен - "
                    f"уже дан доступ к организации '{dept.organization}'"
                )
            elif dept.subdivision and dept.subdivision in self.subdivisions.all():
                redundant.append(
                    f"Отдел '{dept.name}' избыточен - "
                    f"уже дан доступ к подразделению '{dept.subdivision}'"
                )

        if redundant:
            msg = f"⚠️ Избыточные права доступа для {self.user.username}:\n" + "\n".join(redundant)
            logger.warning(msg)

        return redundant

    def get_access_summary(self):
        """Возвращает читаемое описание прав доступа"""
        parts = []

        if self.organizations.exists():
            orgs = ", ".join(o.short_name_ru for o in self.organizations.all())
            parts.append(f"🏢 Организации: {orgs}")

        if self.subdivisions.exists():
            subdivs = ", ".join(s.name for s in self.subdivisions.all())
            parts.append(f"🏭 Подразделения: {subdivs}")

        if self.departments.exists():
            depts = ", ".join(d.name for d in self.departments.all())
            parts.append(f"📂 Отделы: {depts}")

        return "\n".join(parts) if parts else "❌ Нет прав доступа"

    def get_organizations_display(self):
        """
        🔍 Возвращает список организаций в виде строки (пример: "Орг1, Орг2").
        Для обратной совместимости.
        """
        return ", ".join(org.short_name_ru for org in self.organizations.all())
