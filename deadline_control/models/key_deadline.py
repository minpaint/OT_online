# deadline_control/models/key_deadline.py
import calendar
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class KeyDeadlineCategory(models.Model):
    """
    📋 Категория ключевых сроков (группировка мероприятий).
    Например: "Обучение по ОТ", "Инструктажи", "Проверки" и т.д.
    """
    name = models.CharField("Название категории", max_length=255)
    organization = models.ForeignKey(
        'directory.Organization',
        on_delete=models.CASCADE,
        related_name="key_deadline_categories",
        verbose_name="Организация"
    )
    description = models.TextField("Описание", blank=True)
    is_active = models.BooleanField("Активна", default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Категория ключевых сроков"
        verbose_name_plural = "Категории ключевых сроков"
        app_label = 'deadline_control'
        ordering = ['name']
        unique_together = [['organization', 'name']]


class KeyDeadlineItem(models.Model):
    """
    📅 Конкретное мероприятие с периодичностью и датами проведения.
    Привязано к категории ключевых сроков.
    """
    category = models.ForeignKey(
        KeyDeadlineCategory,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Категория"
    )
    name = models.CharField("Наименование мероприятия", max_length=500)
    periodicity_months = models.PositiveIntegerField(
        "Периодичность (месяцев)",
        help_text="Периодичность проведения мероприятия в месяцах"
    )
    current_date = models.DateField(
        "Дата текущего проведения",
        help_text="Дата последнего/текущего проведения мероприятия"
    )
    next_date = models.DateField(
        "Дата следующего проведения",
        blank=True,
        null=True,
        editable=False,
        help_text="Автоматически рассчитывается на основе текущей даты и периодичности"
    )
    responsible_person = models.CharField(
        "Ответственное лицо",
        max_length=255,
        blank=True,
        help_text="ФИО ответственного за проведение мероприятия"
    )
    notes = models.TextField("Примечания", blank=True)

    def __str__(self):
        return f"{self.name} ({self.category.name})"

    @staticmethod
    def _add_months(source_date, months):
        """
        Прибавляет к дате заданное число месяцев, корректно обрабатывая конец месяца.
        """
        month = source_date.month - 1 + months
        year = source_date.year + month // 12
        month = month % 12 + 1
        day = min(source_date.day, calendar.monthrange(year, month)[1])
        return source_date.replace(year=year, month=month, day=day)

    def calculate_next_date(self):
        """
        Вычисляет следующую дату проведения мероприятия.
        """
        if self.current_date and self.periodicity_months:
            return self._add_months(self.current_date, self.periodicity_months)
        return None

    def days_until_next(self):
        """
        Возвращает количество дней до следующего проведения.
        Отрицательное значение означает просрочку.
        """
        if not self.next_date:
            return None
        return (self.next_date - timezone.now().date()).days

    def is_overdue(self):
        """Проверяет, просрочено ли мероприятие"""
        days = self.days_until_next()
        return days is not None and days < 0

    def days_overdue(self):
        """Возвращает количество просроченных дней (положительное число)"""
        days = self.days_until_next()
        if days is None or days >= 0:
            return 0
        return abs(days)

    def is_upcoming(self, warning_days=14):
        """Проверяет, приближается ли срок (по умолчанию за 14 дней)"""
        days = self.days_until_next()
        return days is not None and 0 <= days <= warning_days

    def clean(self):
        """Валидация модели"""
        if self.periodicity_months and self.periodicity_months < 1:
            raise ValidationError({
                'periodicity_months': 'Периодичность должна быть не менее 1 месяца'
            })

    def save(self, *args, **kwargs):
        """Автоматически рассчитываем следующую дату при сохранении"""
        self.next_date = self.calculate_next_date()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Мероприятие"
        verbose_name_plural = "Мероприятия"
        app_label = 'deadline_control'
        ordering = ['next_date', 'name']
