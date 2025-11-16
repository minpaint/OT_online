from django.db import models
from django.core.validators import MinValueValidator, FileExtensionValidator
from django.utils import timezone
from .medical_examination import MedicalExaminationType, HarmfulFactor
from directory.models.position import Position
from directory.models.employee import Employee


class MedicalExaminationNorm(models.Model):
    """
    📋 Справочник эталонных норм медицинских осмотров для должностей.

    Хранит сопоставление наименований должностей с необходимыми видами медосмотров
    и вредными факторами.
    """
    position_name = models.CharField(
        max_length=255,
        verbose_name="Наименование должности",
        db_index=True,
        help_text="Название должности, для которой определяется норма медосмотра"
    )

    harmful_factor = models.ForeignKey(
        HarmfulFactor,
        on_delete=models.CASCADE,
        related_name="medical_norms",
        verbose_name="Вредный фактор",
        help_text="Вредный фактор, определяющий необходимость прохождения медосмотра"
    )

    periodicity_override = models.PositiveIntegerField(
        verbose_name="Переопределение периодичности (месяцы)",
        validators=[MinValueValidator(1)],
        null=True,
        blank=True,
        help_text="Если указано, переопределяет периодичность медосмотра (в месяцах)"
    )

    notes = models.TextField(
        verbose_name="Примечания",
        blank=True,
        help_text="Дополнительная информация о норме"
    )

    class Meta:
        verbose_name = "Норма медосмотра"
        verbose_name_plural = "Нормы медосмотров"
        ordering = ['position_name', 'harmful_factor']
        unique_together = [['position_name', 'harmful_factor']]

    def __str__(self):
        return f"{self.position_name} - {self.harmful_factor}"

    @property
    def periodicity(self):
        """
        Возвращает фактическую периодичность медосмотра (с учетом переопределения)
        """
        if self.periodicity_override:
            return self.periodicity_override
        return self.harmful_factor.periodicity


class PositionMedicalFactor(models.Model):
    """
    🔄 Связь должности с вредными факторами для медосмотров.

    Промежуточная модель для хранения информации о вредных факторах,
    актуальных для конкретной должности, с возможностью переопределения периодичности.
    """
    position = models.ForeignKey(
        Position,
        on_delete=models.CASCADE,
        related_name="medical_factors",
        verbose_name="Должность"
    )

    harmful_factor = models.ForeignKey(
        HarmfulFactor,
        on_delete=models.CASCADE,
        related_name="position_factors",
        verbose_name="Вредный фактор"
    )

    periodicity_override = models.PositiveIntegerField(
        verbose_name="Переопределение периодичности (месяцы)",
        validators=[MinValueValidator(1)],
        null=True,
        blank=True,
        help_text="Если указано, переопределяет периодичность медосмотра (в месяцах)"
    )

    is_disabled = models.BooleanField(
        default=False,
        verbose_name="Отключено",
        help_text="Если отмечено, фактор не применяется для данной должности"
    )

    notes = models.TextField(
        verbose_name="Примечания",
        blank=True,
        help_text="Дополнительная информация о применении фактора к должности"
    )

    class Meta:
        verbose_name = "Вредный фактор должности"
        verbose_name_plural = "Вредные факторы должностей"
        unique_together = [['position', 'harmful_factor']]
        ordering = ['position', 'harmful_factor']

    def __str__(self):
        status = " (отключено)" if self.is_disabled else ""
        return f"{self.position} - {self.harmful_factor}{status}"

    @property
    def periodicity(self):
        """
        Возвращает фактическую периодичность медосмотра (с учетом переопределения)
        """
        if self.periodicity_override:
            return self.periodicity_override
        return self.harmful_factor.periodicity


class EmployeeMedicalExamination(models.Model):
    """
    👨‍⚕️ Медицинские осмотры сотрудников.

    Хранит информацию о пройденных и запланированных медосмотрах сотрудников.
    """
    STATUS_CHOICES = [
        ('completed', 'Пройден'),
        ('expired', 'Просрочен'),
        ('scheduled', 'Запланирован'),
        ('to_issue', 'Нужно выдать направление')
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="medical_examinations",
        verbose_name="Сотрудник",
        help_text="Сотрудник, для которого регистрируется медосмотр"
    )

    harmful_factor = models.ForeignKey(
        HarmfulFactor,
        on_delete=models.PROTECT,
        related_name="employee_examinations",
        verbose_name="Вредный фактор",
        help_text="Вредный фактор, по которому проводился медосмотр"
    )

    date_completed = models.DateField(
        verbose_name="Дата прохождения",
        help_text="Дата фактического прохождения медосмотра"
    )

    next_date = models.DateField(
        verbose_name="Дата следующего медосмотра",
        help_text="Плановая дата следующего медосмотра"
    )

    medical_certificate = models.FileField(
        upload_to='medical_certificates/%Y/%m/',
        verbose_name="Скан справки",
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )

    status = models.CharField(
        max_length=20,
        verbose_name="Статус",
        choices=STATUS_CHOICES,
        default='completed',
        help_text="Текущий статус медосмотра"
    )

    notes = models.TextField(
        verbose_name="Примечания",
        blank=True,
        help_text="Дополнительная информация о медосмотре"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания записи"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления записи"
    )

    class Meta:
        verbose_name = "Медосмотр сотрудника"
        verbose_name_plural = "Медосмотры сотрудников"
        ordering = ['-date_completed', 'employee']

    def __str__(self):
        return f"{self.employee} - {self.harmful_factor} ({self.date_completed})"

    @property
    def is_expired(self):
        """Проверяет, истек ли срок действия медосмотра"""
        return self.next_date < timezone.now().date()

    @property
    def days_remaining(self):
        """Возвращает количество дней до следующего медосмотра"""
        today = timezone.now().date()
        if self.next_date < today:
            return 0
        return (self.next_date - today).days

    def save(self, *args, **kwargs):
        """Переопределяем save для автоматического обновления статуса"""
        today = timezone.now().date()

        # Обновляем статус в зависимости от даты
        if self.next_date < today:
            self.status = 'expired'

        super().save(*args, **kwargs)