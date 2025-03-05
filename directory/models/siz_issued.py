from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class SIZIssued(models.Model):
    """
    🛡️ Модель для хранения информации о выданных сотрудникам СИЗ

    Хранит информацию о каждой выдаче СИЗ сотруднику, включая:
    - Кому выдано
    - Какое СИЗ выдано
    - Когда выдано
    - Количество
    - Процент износа
    - Срок использования и т.д.
    """
    employee = models.ForeignKey(
        'directory.Employee',
        on_delete=models.CASCADE,
        related_name='issued_siz',
        verbose_name="Сотрудник"
    )
    siz = models.ForeignKey(
        'directory.SIZ',
        on_delete=models.CASCADE,
        related_name='issues',
        verbose_name="СИЗ"
    )
    issue_date = models.DateField(
        verbose_name="Дата выдачи",
        default=timezone.now
    )
    quantity = models.PositiveIntegerField(
        verbose_name="Количество",
        default=1
    )
    wear_percentage = models.PositiveIntegerField(
        verbose_name="Процент износа",
        default=0,
        help_text="Укажите процент износа от 0 до 100"
    )
    cost = models.DecimalField(
        verbose_name="Стоимость",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    replacement_date = models.DateField(
        verbose_name="Дата замены/списания",
        null=True,
        blank=True
    )
    is_returned = models.BooleanField(
        verbose_name="Возвращено",
        default=False
    )
    return_date = models.DateField(
        verbose_name="Дата возврата",
        null=True,
        blank=True
    )
    notes = models.TextField(
        verbose_name="Примечания",
        blank=True
    )

    # Для учета условий выдачи (например, "При работе на высоте")
    condition = models.CharField(
        verbose_name="Условие выдачи",
        max_length=255,
        blank=True,
        help_text="Условие, при котором выдано СИЗ"
    )

    # Для подписи о получении
    received_signature = models.BooleanField(
        verbose_name="Подпись о получении",
        default=False
    )

    class Meta:
        verbose_name = "Выданное СИЗ"
        verbose_name_plural = "Выданные СИЗ"
        ordering = ['-issue_date', 'employee__full_name_nominative']

    def __str__(self):
        return f"{self.siz} - {self.employee} ({self.issue_date})"

    def clean(self):
        """
        🧪 Валидация данных перед сохранением

        Проверки:
        - Если СИЗ возвращено, должна быть указана дата возврата
        - Дата возврата не может быть раньше даты выдачи
        - Процент износа не может быть больше 100
        """
        if self.is_returned and not self.return_date:
            raise ValidationError({
                'return_date': 'Если СИЗ возвращено, необходимо указать дату возврата'
            })

        if self.return_date and self.issue_date and self.return_date < self.issue_date:
            raise ValidationError({
                'return_date': 'Дата возврата не может быть раньше даты выдачи'
            })

        if self.wear_percentage > 100:
            raise ValidationError({
                'wear_percentage': 'Процент износа не может быть больше 100'
            })

    def save(self, *args, **kwargs):
        """
        💾 Метод сохранения с валидацией
        """
        self.clean()
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        """
        ✅ Проверка, является ли выданное СИЗ активным (не возвращено и не заменено)
        """
        return not self.is_returned and not self.replacement_date

    @property
    def wear_status(self):
        """
        📊 Получение текстового статуса износа
        """
        if self.wear_percentage < 30:
            return "Хорошее состояние"
        elif self.wear_percentage < 70:
            return "Удовлетворительное состояние"
        else:
            return "Требует замены"