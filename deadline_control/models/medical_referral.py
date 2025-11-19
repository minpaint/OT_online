from django.db import models
from django.utils import timezone


class MedicalReferral(models.Model):
    """
    📋 Направление на медицинский осмотр.

    Регистрирует факт выдачи направления сотруднику с сохранением данных
    на момент выдачи и списка вредных факторов.
    """

    employee = models.ForeignKey(
        'directory.Employee',
        on_delete=models.CASCADE,
        related_name="medical_referrals",
        verbose_name="Сотрудник"
    )

    # Данные на момент выдачи (могут отличаться от текущих)
    employee_birth_date = models.DateField(
        verbose_name="Дата рождения",
        help_text="Дата рождения сотрудника на момент выдачи"
    )

    employee_address = models.TextField(
        verbose_name="Место проживания",
        help_text="Адрес проживания сотрудника на момент выдачи"
    )

    # Вредные факторы (M2M)
    harmful_factors = models.ManyToManyField(
        'deadline_control.HarmfulFactor',
        related_name="referrals",
        verbose_name="Вредные факторы",
        blank=True
    )

    # Метаданные выдачи
    issue_date = models.DateField(
        verbose_name="Дата выдачи",
        default=timezone.now,
        help_text="Дата выдачи направления"
    )

    issued_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name="issued_referrals",
        verbose_name="Кем выдано"
    )

    # Сгенерированный документ
    document = models.FileField(
        upload_to='medical_referrals/%Y/%m/',
        verbose_name="Документ направления",
        blank=True,
        null=True
    )

    notes = models.TextField(
        verbose_name="Примечания",
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Направление на медосмотр"
        verbose_name_plural = "Направления на медосмотры"
        ordering = ['-issue_date', '-created_at']

    def __str__(self):
        return f"Направление #{self.pk} - {self.employee} ({self.issue_date})"

    @property
    def organization(self):
        """Возвращает организацию сотрудника"""
        return self.employee.organization
