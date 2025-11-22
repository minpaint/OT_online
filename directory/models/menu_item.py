# directory/models/menu_item.py
"""
Модель для управления пунктами меню и правами доступа к ним.
"""
from django.db import models


class MenuItem(models.Model):
    """
    🍔 Пункт меню системы с поддержкой иерархии

    Используется для управления доступом к различным разделам системы.
    """

    LOCATION_CHOICES = [
        ('sidebar', 'Боковое меню'),
        ('top', 'Верхнее меню'),
        ('both', 'Оба меню'),
    ]

    name = models.CharField(
        max_length=100,
        verbose_name="Название",
        help_text="Название пункта меню, отображаемое пользователю"
    )

    icon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Иконка",
        help_text="Emoji или CSS класс иконки (например: 👥, 🔧)"
    )

    url_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="URL name",
        help_text="Django URL name (например: directory:employees:list) или внешний URL"
    )

    url = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Прямой URL",
        help_text="Прямой URL (если url_name не указан)"
    )

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name="Родительский пункт",
        help_text="Для создания вложенных меню"
    )

    order = models.IntegerField(
        default=0,
        verbose_name="Порядок",
        help_text="Порядок отображения (меньше = выше)"
    )

    location = models.CharField(
        max_length=20,
        choices=LOCATION_CHOICES,
        default='sidebar',
        verbose_name="Расположение",
        help_text="Где отображается этот пункт меню"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен",
        help_text="Неактивные пункты не отображаются никому"
    )

    requires_auth = models.BooleanField(
        default=True,
        verbose_name="Требует авторизации",
        help_text="Показывать только авторизованным пользователям"
    )

    is_separator = models.BooleanField(
        default=False,
        verbose_name="Разделитель",
        help_text="Визуальный разделитель между группами пунктов"
    )

    description = models.TextField(
        blank=True,
        verbose_name="Описание",
        help_text="Описание для администраторов"
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
        verbose_name = "Пункт меню"
        verbose_name_plural = "Пункты меню"
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['parent', 'order']),
            models.Index(fields=['location', 'is_active']),
        ]

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} → {self.name}"
        return self.name

    def get_full_path(self):
        """Возвращает полный путь в иерархии меню"""
        if self.parent:
            return f"{self.parent.get_full_path()} > {self.name}"
        return self.name

    def get_children(self):
        """Возвращает активные дочерние пункты"""
        return self.children.filter(is_active=True).order_by('order')

    def has_children(self):
        """Проверяет наличие дочерних пунктов"""
        return self.children.filter(is_active=True).exists()

    def get_url(self):
        """Возвращает URL пункта меню"""
        if self.url_name:
            from django.urls import reverse, NoReverseMatch
            try:
                return reverse(self.url_name)
            except NoReverseMatch:
                return '#'
        return self.url or '#'

    def is_visible_for_user(self, user):
        """
        Проверяет, виден ли пункт меню для пользователя.

        Args:
            user: объект User

        Returns:
            bool: True если пункт виден
        """
        # Неактивные пункты не видны никому
        if not self.is_active:
            return False

        # Проверка авторизации
        if self.requires_auth and not user.is_authenticated:
            return False

        # Суперпользователи видят все
        if user.is_superuser:
            return True

        # Проверяем права через профиль
        if hasattr(user, 'profile'):
            profile = user.profile
            # Если у пользователя нет явных ограничений - показываем все
            if not profile.visible_menu_items.exists():
                return True
            # Если есть ограничения - проверяем доступ
            return self in profile.visible_menu_items.all()

        # По умолчанию показываем
        return True
