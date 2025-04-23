# directory/models/hiring.py
from django.db import models
from django.utils.translation import gettext_lazy as _


class EmployeeHiring(models.Model):
    """
    📝 Модель для хранения информации о приеме сотрудника на работу.
    """
    HIRING_TYPE_CHOICES = [
        ('new', '🆕 Новый сотрудник'),
        ('transfer', '↔️ Перевод'),
        ('return', '↩️ Возврат из отпуска'),
        ('contractor', '📄 Договор подряда'),
        ('part_time', '⌛ Совместительство'),
    ]

    employee = models.ForeignKey(
        'directory.Employee',
        on_delete=models.CASCADE,
        related_name='hirings',
        verbose_name=_("Сотрудник")
    )

    hiring_date = models.DateField(
        verbose_name=_("Дата приема"),
        help_text=_("Дата приема на работу")
    )

    start_date = models.DateField(
        verbose_name=_("Дата начала работы"),
        help_text=_("Дата фактического начала работы")
    )

    hiring_type = models.CharField(
        max_length=20,
        choices=HIRING_TYPE_CHOICES,
        default='new',
        verbose_name=_("Вид приема")
    )

    organization = models.ForeignKey(
        'directory.Organization',
        on_delete=models.CASCADE,
        verbose_name=_("Организация"),
        related_name='hirings'
    )

    subdivision = models.ForeignKey(
        'directory.StructuralSubdivision',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Подразделение"),
        related_name='hirings'
    )

    department = models.ForeignKey(
        'directory.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Отдел"),
        related_name='hirings'
    )

    position = models.ForeignKey(
        'directory.Position',
        on_delete=models.PROTECT,
        verbose_name=_("Должность"),
        related_name='hirings'
    )

    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Кем создан"),
        related_name='created_hirings'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Дата создания")
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Дата обновления")
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_("Примечания")
    )

    documents = models.ManyToManyField(
        'directory.GeneratedDocument',
        blank=True,
        related_name='hiring_records',
        verbose_name=_("Сгенерированные документы")
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Активен")
    )

    class Meta:
        verbose_name = _("Прием на работу")
        verbose_name_plural = _("Приемы на работу")
        ordering = ['-hiring_date', 'employee__full_name_nominative']

    def __str__(self):
        return f"{self.employee.full_name_nominative} - {self.get_hiring_type_display()} ({self.hiring_date})"

    def get_hierarchy_path(self):
        """Возвращает иерархический путь для отображения"""
        parts = [self.organization.short_name_ru]
        if self.subdivision:
            parts.append(self.subdivision.name)
        if self.department:
            parts.append(self.department.name)
        return " → ".join(parts)