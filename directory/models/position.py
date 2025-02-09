from django.db import models
from django.core.exceptions import ValidationError


class Position(models.Model):
    """
    👔 Модель для хранения информации о должностях.
    """
    ELECTRICAL_GROUP_CHOICES = [
        ("I", "I"),
        ("II", "II"),
        ("III", "III"),
        ("IV", "IV"),
        ("V", "V"),
    ]
    COMMISSION_ROLE_CHOICES = [
        ('chairman', '👑 Председатель комиссии'),
        ('member', '👤 Член комиссии'),
        ('secretary', '📝 Секретарь комиссии'),
        ('none', '❌ Не участвует в комиссии'),
    ]

    commission_role = models.CharField(
        "Роль в комиссии",
        max_length=10,
        choices=COMMISSION_ROLE_CHOICES,
        default='none',
        help_text="Укажите роль сотрудника в комиссии"
    )
    position_name = models.CharField(max_length=255, verbose_name="Название")
    organization = models.ForeignKey(
        'directory.Organization',
        on_delete=models.PROTECT,
        related_name="positions",
        verbose_name="Организация"
    )
    subdivision = models.ForeignKey(
        'directory.StructuralSubdivision',
        on_delete=models.PROTECT,
        related_name="positions",
        verbose_name="Структурное подразделение",
        null=True,
        blank=True
    )
    department = models.ForeignKey(
        'directory.Department',
        on_delete=models.PROTECT,
        related_name="positions",
        verbose_name="Отдел",
        null=True,
        blank=True
    )

    safety_instructions_numbers = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Номера инструкций по ОТ"
    )
    electrical_safety_group = models.CharField(
        max_length=4,
        choices=ELECTRICAL_GROUP_CHOICES,
        blank=True,
        verbose_name="Группа по электробезопасности"
    )
    internship_period_days = models.PositiveIntegerField(
        default=0,
        verbose_name="Срок стажировки (дни)"
    )

    is_responsible_for_safety = models.BooleanField(
        default=False,
        verbose_name="Ответственный за ОТ"
    )
    is_electrical_personnel = models.BooleanField(
        default=False,
        verbose_name="Электротехнический персонал"
    )
    can_be_internship_leader = models.BooleanField(
        default=False,
        verbose_name="Может быть руководителем стажировки"
    )

    documents = models.ManyToManyField(
        'directory.Document',
        blank=True,
        related_name="positions",
        verbose_name="Документы"
    )
    equipment = models.ManyToManyField(
        'directory.Equipment',
        blank=True,
        related_name="positions",
        verbose_name="Оборудование"
    )

    class Meta:
        verbose_name = "Профессия/должность"
        verbose_name_plural = "Профессии/должности"
        ordering = ['position_name']
        unique_together = [
            ['position_name', 'organization', 'subdivision', 'department']
        ]

    def clean(self):
        if self.department:
            if not self.subdivision:
                raise ValidationError({
                    'department': 'Нельзя указать отдел без структурного подразделения'
                })
            if self.department.organization != self.organization:
                raise ValidationError({
                    'department': 'Отдел должен принадлежать выбранной организации'
                })
            if self.department.subdivision != self.subdivision:
                raise ValidationError({
                    'department': 'Отдел должен принадлежать выбранному подразделению'
                })

        if self.subdivision and self.subdivision.organization != self.organization:
            raise ValidationError({
                'subdivision': 'Подразделение должно принадлежать выбранной организации'
            })

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        parts = [self.position_name]
        if self.department:
            parts.append(f"({self.department.name})")
        elif self.subdivision:
            parts.append(f"({self.subdivision.name})")
        else:
            parts.append(f"({self.organization.short_name_ru})")
        return " ".join(parts)