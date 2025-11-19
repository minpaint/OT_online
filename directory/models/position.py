from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Count


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

    contract_work_name = models.TextField(
        "🔨 Наименование работы по договору подряда",
        blank=True,
        help_text="Укажите наименование работы, выполняемой по договору подряда"
    )

    contract_safety_instructions = models.CharField(
        "⚠️ Инструкции по охране труда по договору подряда",
        max_length=255,
        blank=True,
        help_text="Укажите номера инструкций по охране труда для данного вида работ"
    )

    position_name = models.CharField(
        max_length=255,
        verbose_name="Название"
    )
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

    can_sign_orders = models.BooleanField(
        default=False,
        verbose_name="Может подписывать распоряжения",
        help_text="Указывает, может ли сотрудник с этой должностью подписывать распоряжения"
    )

    documents = models.ManyToManyField(
        'directory.Document',
        blank=True,
        related_name="positions",
        verbose_name="Документы"
    )
    equipment = models.ManyToManyField(
        'deadline_control.Equipment',
        blank=True,
        related_name="positions",
        verbose_name="Оборудование"
    )
    medical_harmful_factors = models.ManyToManyField(
        'deadline_control.HarmfulFactor',
        through='deadline_control.PositionMedicalFactor',
        related_name='positions',
        verbose_name="Вредные факторы медосмотров",
        blank=True
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
        if not self.department:
            if self.subdivision:
                parts.append(f"({self.subdivision.name})")
            else:
                parts.append(f"({self.organization.short_name_ru})")
        return " ".join(parts)

    def get_full_path(self):
        parts = [self.organization.short_name_ru or self.organization.full_name_ru]
        if self.subdivision:
            parts.append(self.subdivision.name)
        if self.department:
            parts.append(self.department.name)
        parts.append(self.position_name)
        return " → ".join(parts)

    @classmethod
    def find_reference_norms(cls, position_name):
        positions = cls.objects.filter(position_name__exact=position_name)
        from directory.models.siz import SIZNorm
        norms = SIZNorm.objects.filter(position__in=positions).select_related('siz')
        return norms
