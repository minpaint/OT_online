from django.db import models
from .organization import Organization


class Department(models.Model):
    """Структурное подразделение"""

    # Основные поля
    name = models.CharField(
        'Наименование структурного подразделения',
        max_length=255
    )
    short_name = models.CharField(
        'Сокращенное наименование',
        max_length=100,
        blank=True
    )

    # Связи
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        verbose_name='Организация',
        related_name='departments'
    )

    # Служебные поля
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Структурное подразделение'
        verbose_name_plural = 'Структурные подразделения'
        ordering = ['name']
        # Уникальность наименования в рамках организации
        unique_together = ['organization', 'name']

    def __str__(self):
        return f"{self.name} ({self.organization.short_name_ru})"

    def get_full_name(self):
        """Полное наименование с организацией"""
        return f"{self.organization.short_name_ru} - {self.name}"