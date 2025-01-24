from django.db import models
from .department import Department
from .organization import Organization


class Division(models.Model):
    """Отдел"""

    # Основные поля
    name = models.CharField(
        'Наименование отдела',
        max_length=255
    )
    short_name = models.CharField(
        'Сокращенное наименование',
        max_length=100,
        blank=True
    )

    # Связи
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        verbose_name='Структурное подразделение',
        related_name='divisions'
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        verbose_name='Организация',
        related_name='divisions'
    )

    # Служебные поля
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Отдел'
        verbose_name_plural = 'Отделы'
        ordering = ['name']
        # Уникальность наименования в рамках структурного подразделения
        unique_together = ['department', 'name']

    def __str__(self):
        return f"{self.name} ({self.department.name})"

    def get_full_name(self):
        """Полное наименование с иерархией"""
        return f"{self.organization.short_name_ru} - {self.department.name} - {self.name}"

    def save(self, *args, **kwargs):
        """
        Автоматическое заполнение организации из структурного подразделения
        """
        if self.department and not self.organization_id:
            self.organization = self.department.organization
        super().save(*args, **kwargs)