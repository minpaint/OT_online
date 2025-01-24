from django.db import models
from .organizational_unit import OrganizationalUnit


class Organization(models.Model):
    """Организация"""

    # Связь с организационной структурой
    unit = models.OneToOneField(
        OrganizationalUnit,
        on_delete=models.CASCADE,
        verbose_name='Организационная единица'
    )

    # Русская локализация
    name_ru = models.CharField('Полное наименование организации', max_length=255)
    short_name_ru = models.CharField('Сокращенное наименование организации', max_length=100)
    requisites_ru = models.TextField('Реквизиты на русском языке', blank=True)

    # Белорусская локализация
    name_by = models.CharField('Наименование организации на белорусском языке', max_length=255)
    short_name_by = models.CharField('Сокращенное наименование на белорусском языке', max_length=100, blank=True)
    requisites_by = models.TextField('Реквизиты на белорусском языке', blank=True)

    # Общие поля
    inn = models.CharField('УНП', max_length=9, unique=True)

    # Служебные поля
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Организация'
        verbose_name_plural = 'Организации'
        ordering = ['short_name_ru']

    def __str__(self):
        return self.short_name_ru

    def save(self, *args, **kwargs):
        if not self.unit_id:
            # Создаем организационную единицу при создании организации
            unit = OrganizationalUnit.objects.create(
                name=self.short_name_ru,
                unit_type='organization'
            )
            self.unit = unit
        super().save(*args, **kwargs)