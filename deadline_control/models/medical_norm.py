import calendar
from django.db import models
from django.core.validators import MinValueValidator, FileExtensionValidator
from django.utils import timezone
from .medical_examination import MedicalExaminationType, HarmfulFactor


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
        verbose_name = "Вредный фактор профессии"
        verbose_name_plural = "Вредные факторы по профессиям"
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
        'directory.Position',
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
        'directory.Employee',
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
        help_text="Дата фактического прохождения медосмотра",
        null=True,
        blank=True
    )

    next_date = models.DateField(
        verbose_name="Дата следующего медосмотра",
        help_text="Плановая дата следующего медосмотра",
        null=True,
        blank=True
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

    is_disabled = models.BooleanField(
        default=False,
        verbose_name="Не требуется",
        help_text="Если отмечено, медосмотр по этому фактору не требуется для данного сотрудника"
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

    def days_until_next(self):
        """
        Computes days until the next medical examination.
        Returns None if no date is set.
        """
        if not self.next_date:
            return None
        return (self.next_date - timezone.now().date()).days

    def days_overdue(self):
        """Возвращает количество просроченных дней (положительное число)"""
        days = self.days_until_next()
        if days is None or days >= 0:
            return 0
        return abs(days)

    @property
    def is_expired(self):
        """Проверяет, истек ли срок действия медосмотра"""
        if not self.next_date:
            return False
        return self.next_date < timezone.now().date()

    @property
    def days_remaining(self):
        """Возвращает количество дней до следующего медосмотра"""
        if not self.next_date:
            return None
        today = timezone.now().date()
        if self.next_date < today:
            return 0
        return (self.next_date - today).days

    @staticmethod
    def _add_months(source_date, months):
        """
        Прибавляет к дате заданное число месяцев, корректно обрабатывая конец месяца.
        Аналогично Equipment._add_months()
        """
        month = source_date.month - 1 + months
        year = source_date.year + month // 12
        month = month % 12 + 1
        day = min(source_date.day, calendar.monthrange(year, month)[1])
        return source_date.replace(year=year, month=month, day=day)

    def perform_examination(self, examination_date=None):
        """
        Проводит медицинский осмотр:
        - записывает дату прохождения (date_completed)
        - автоматически вычисляет next_date на основе периодичности вредного фактора
        - обновляет статус на 'completed'

        Аналогично Equipment.update_maintenance()
        """
        exam_date = examination_date or timezone.now().date()

        self.date_completed = exam_date

        # Получаем периодичность из вредного фактора (или переопределения)
        periodicity = self.harmful_factor.periodicity

        # Рассчитываем следующую дату
        self.next_date = self._add_months(exam_date, periodicity)
        self.status = 'completed'
        self.save()

    def save(self, *args, **kwargs):
        """Переопределяем save для автоматического обновления статуса"""
        today = timezone.now().date()

        # Обновляем статус в зависимости от даты
        if not self.date_completed or not self.next_date:
            # Если даты не указаны - нужно выдать направление
            self.status = 'to_issue'
        elif self.next_date < today:
            # Если срок истек
            self.status = 'expired'
        else:
            # Если дата есть и срок не истек
            self.status = 'completed'

        super().save(*args, **kwargs)
