from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class SIZ(models.Model):
    """
    🛡️ Модель средства индивидуальной защиты (СИЗ)
    """
    name = models.CharField(
        "Наименование СИЗ",
        max_length=255
    )
    classification = models.CharField(
        "Классификация (маркировка)",
        max_length=100,
        help_text="Маркировка СИЗ по защитным свойствам или конструктивным особенностям"
    )
    unit = models.CharField(
        "Единица измерения",
        max_length=50,
        default="шт."
    )
    wear_period = models.PositiveIntegerField(
        "Срок носки в месяцах",
        default=12,
        help_text="0 означает 'До износа'"
    )

    class Meta:
        verbose_name = "Средство индивидуальной защиты"
        verbose_name_plural = "Средства индивидуальной защиты"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.classification})"

    @property
    def wear_period_display(self):
        """🕒 Отображение срока носки (с учетом 'До износа')"""
        return "До износа" if self.wear_period == 0 else f"{self.wear_period}"


class SIZNorm(models.Model):
    """
    📋 Норма выдачи СИЗ для профессии
    """
    position = models.ForeignKey(
        'directory.Position',
        on_delete=models.CASCADE,
        related_name="siz_norms",
        verbose_name="Профессия/должность"
    )
    siz = models.ForeignKey(
        SIZ,
        on_delete=models.CASCADE,
        related_name="norms",
        verbose_name="СИЗ"
    )
    quantity = models.PositiveIntegerField(
        "Количество",
        default=1
    )
    condition = models.CharField(
        "Условие выдачи",
        max_length=255,
        blank=True,
        help_text="Например: 'При влажной уборке помещений', 'При работе на высоте' и т.д."
    )
    order = models.PositiveIntegerField(
        "Порядок отображения",
        default=0
    )

    class Meta:
        verbose_name = "Норма выдачи СИЗ"
        verbose_name_plural = "Нормы выдачи СИЗ"
        unique_together = [['position', 'siz', 'condition']]
        ordering = ['position', 'condition', 'order', 'siz__name']

    def __str__(self):
        if self.condition:
            return f"{self.position} - {self.siz} ({self.condition})"
        return f"{self.position} - {self.siz}"

    @property
    def get_condition_display(self):
        """📝 Получение текста условия выдачи"""
        return self.condition or "Основная норма"


# Сигнал для автоматического копирования норм СИЗ
@receiver(post_save, sender='directory.Position')
def copy_reference_siz_norms(sender, instance, created, **kwargs):
    """
    🔄 Автоматическое копирование эталонных норм СИЗ при создании новой должности
    """
    from directory.models.position import Position

    # Только для новых должностей
    if created:
        # Находим эталонные нормы для этой профессии
        reference_norms = Position.find_reference_norms(instance.position_name)

        # Если есть эталонные нормы, копируем их для новой должности
        for norm in reference_norms:
            SIZNorm.objects.create(
                position=instance,
                siz=norm.siz,
                quantity=norm.quantity,
                condition=norm.condition,
                order=norm.order
            )