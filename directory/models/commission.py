# directory/models/commission.py
from django.db import models


class Commission(models.Model):
    """
    🔍 Модель для хранения комиссий по проверке знаний ОТ.

    Комиссии могут быть привязаны к организации, подразделению или отделу.
    """
    COMMISSION_TYPE_CHOICES = [
        ('ot', '🛡️ Охрана труда'),
        ('eb', '⚡ Электробезопасность'),
        ('pb', '🔥 Пожарная безопасность'),
        ('other', '📋 Иная'),
    ]

    name = models.CharField("Наименование комиссии", max_length=255)
    commission_type = models.CharField(
        "Тип комиссии",
        max_length=10,
        choices=COMMISSION_TYPE_CHOICES,
        default='ot'
    )
    is_active = models.BooleanField("Активна", default=True)

    # Привязка к организационной структуре (только один из этих уровней)
    organization = models.ForeignKey(
        'directory.Organization',
        on_delete=models.CASCADE,
        related_name="commissions",
        verbose_name="Организация",
        null=True,
        blank=True
    )
    subdivision = models.ForeignKey(
        'directory.StructuralSubdivision',
        on_delete=models.CASCADE,
        related_name="commissions",
        verbose_name="Структурное подразделение",
        null=True,
        blank=True
    )
    department = models.ForeignKey(
        'directory.Department',
        on_delete=models.CASCADE,
        related_name="commissions",
        verbose_name="Отдел",
        null=True,
        blank=True
    )

    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        verbose_name = "Комиссия по проверке знаний"
        verbose_name_plural = "Комиссии по проверке знаний"
        ordering = ['-is_active', 'name']

    def __str__(self):
        level = ""
        if self.department:
            level = f" ({self.department.name})"
        elif self.subdivision:
            level = f" ({self.subdivision.name})"
        elif self.organization:
            level = f" ({self.organization.short_name_ru})"
        return f"{self.name}{level}"

    def clean(self):
        """Валидация модели: комиссия может быть привязана только к одному уровню."""
        from django.core.exceptions import ValidationError
        levels = [
            self.organization is not None,
            self.subdivision is not None,
            self.department is not None
        ]
        if sum(levels) > 1:
            raise ValidationError(
                "Комиссия может быть привязана только к одному уровню: "
                "организация, подразделение или отдел"
            )

        # Проверка согласованности: если указан отдел, должно быть указано подразделение
        if self.department and not self.subdivision:
            raise ValidationError({
                'department': 'Для отдела должно быть указано структурное подразделение'
            })

        # Проверка согласованности: если указано подразделение, должна быть указана организация
        if self.subdivision and not self.organization:
            raise ValidationError({
                'subdivision': 'Для подразделения должна быть указана организация'
            })

        # Проверка согласованности отдела и подразделения, если оба указаны
        if self.department and self.subdivision and self.department.subdivision != self.subdivision:
            raise ValidationError({
                'department': 'Отдел должен принадлежать указанному подразделению'
            })

        # Проверка согласованности подразделения и организации, если оба указаны
        if self.subdivision and self.organization and self.subdivision.organization != self.organization:
            raise ValidationError({
                'subdivision': 'Подразделение должно принадлежать указанной организации'
            })

        # Дополнительная проверка, что хоть один уровень указан
        if sum(levels) == 0:
            raise ValidationError(
                "Необходимо указать уровень комиссии: организация, подразделение или отдел"
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def get_members(self):
        """Возвращает всех участников комиссии с учетом их ролей."""
        return self.members.select_related('employee', 'employee__position').order_by('role')

    def get_chairman(self):
        """Возвращает председателя комиссии."""
        return self.members.filter(role='chairman').select_related(
            'employee', 'employee__position'
        ).first()

    def get_secretary(self):
        """Возвращает секретаря комиссии."""
        return self.members.filter(role='secretary').select_related(
            'employee', 'employee__position'
        ).first()

    def get_committee_members(self):
        """Возвращает членов комиссии (без председателя и секретаря)."""
        return self.members.filter(role='member').select_related(
            'employee', 'employee__position'
        ).all()


class CommissionMember(models.Model):
    """
    👤 Модель для хранения состава комиссии.

    Каждый участник может иметь роль (председатель, член, секретарь).
    """
    ROLE_CHOICES = [
        ('chairman', '👑 Председатель комиссии'),
        ('member', '👤 Член комиссии'),
        ('secretary', '📝 Секретарь комиссии'),
    ]

    commission = models.ForeignKey(
        Commission,
        on_delete=models.CASCADE,
        related_name="members",
        verbose_name="Комиссия"
    )
    employee = models.ForeignKey(
        'directory.Employee',
        on_delete=models.CASCADE,
        related_name="commission_roles",
        verbose_name="Сотрудник"
    )
    role = models.CharField(
        "Роль в комиссии",
        max_length=10,
        choices=ROLE_CHOICES,
        default='member'
    )
    is_active = models.BooleanField("Активен", default=True)

    class Meta:
        verbose_name = "Участник комиссии"
        verbose_name_plural = "Участники комиссии"
        ordering = ['role', 'employee__full_name_nominative']
        # Участник может быть только в одной роли в рамках одной комиссии
        unique_together = [['commission', 'employee', 'role']]

    def __str__(self):
        role_display = dict(self.ROLE_CHOICES).get(self.role, self.role)
        return f"{self.employee.full_name_nominative} - {role_display} ({self.commission.name})"

    # Функция для получения форматированного имени и должности
    def get_formatted_name(self):
        """Возвращает строку вида 'Иванов И.И., директор'"""
        from directory.utils.declension import get_initials_from_name

        name_initials = get_initials_from_name(self.employee.full_name_nominative)
        position = self.employee.position.position_name.lower() if self.employee.position else ""

        if position:
            return f"{name_initials}, {position}"
        return name_initials