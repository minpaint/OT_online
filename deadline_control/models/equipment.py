# deadline_control/models/equipment.py
import calendar
from datetime import timedelta
from django.db import models
from django.utils import timezone


class Equipment(models.Model):
    """
    ⚙️ Модель для хранения оборудования и управления техническим обслуживанием.
    Оборудование привязано к организации, подразделению и отделу.
    Содержит информацию о техническом обслуживании.
    """
    equipment_name = models.CharField("Наименование оборудования", max_length=255)
    inventory_number = models.CharField("Инвентарный номер", max_length=100, unique=True)
    organization = models.ForeignKey(
        'directory.Organization',
        on_delete=models.CASCADE,
        related_name="deadline_equipment",
        verbose_name="Организация"
    )
    subdivision = models.ForeignKey(
        'directory.StructuralSubdivision',
        on_delete=models.CASCADE,
        related_name="deadline_equipment",
        verbose_name="Структурное подразделение",
        null=True,
        blank=True
    )
    department = models.ForeignKey(
        'directory.Department',
        on_delete=models.SET_NULL,
        related_name="deadline_equipment",
        null=True,
        blank=True,
        verbose_name="Отдел"
    )

    # Поля для технического обслуживания
    last_maintenance_date = models.DateField("Дата последнего ТО", null=True, blank=True)
    next_maintenance_date = models.DateField("Дата следующего ТО", null=True, blank=True)
    maintenance_period_months = models.PositiveIntegerField("Периодичность ТО (месяцев)", default=12)
    maintenance_history = models.JSONField(
        "История ТО",
        default=list,
        blank=True,
        help_text="Список записей: {'date': 'YYYY-MM-DD', 'comment': '...'}"
    )

    MAINTENANCE_STATUS_CHOICES = [
        ('operational', 'Исправно'),
        ('needs_maintenance', 'Требует ТО'),
        ('in_maintenance', 'На обслуживании'),
        ('out_of_order', 'Неисправно'),
    ]
    maintenance_status = models.CharField(
        "Статус обслуживания",
        max_length=20,
        choices=MAINTENANCE_STATUS_CHOICES,
        default='operational'
    )

    def __str__(self):
        return f"{self.equipment_name} (инв.№ {self.inventory_number})"

    @staticmethod
    def _add_months(source_date, months):
        """
        Прибавляет к дате заданное число месяцев, корректно обрабатывая конец месяца.
        """
        month = source_date.month - 1 + months
        year = source_date.year + month // 12
        month = month % 12 + 1
        day = min(source_date.day, calendar.monthrange(year, month)[1])
        return source_date.replace(year=year, month=month, day=day)

    def update_maintenance(self, new_date=None, comment=''):
        """
        Обновляет информацию о ТО оборудования:
        - сохраняет предыдущую дату + комментарий в history,
        - записывает новую last_maintenance_date,
        - вычисляет next_maintenance_date, прибавляя months.
        """
        maintenance_date = new_date or timezone.now().date()

        if self.last_maintenance_date:
            history = self.maintenance_history if isinstance(self.maintenance_history, list) else []
            history.append({
                'date': self.last_maintenance_date.isoformat(),
                'comment': comment or ''
            })
            self.maintenance_history = history[-10:]

        self.last_maintenance_date = maintenance_date
        self.next_maintenance_date = self._add_months(
            maintenance_date, self.maintenance_period_months
        )
        self.maintenance_status = 'operational'
        self.save()

    def is_maintenance_required(self):
        """Проверяет, требуется ли ТО (за 7 дней до)"""
        today = timezone.now().date()
        return bool(
            self.next_maintenance_date and
            self.next_maintenance_date <= (today + timedelta(days=7))
        )

    def days_until_maintenance(self):
        """Возвращает количество дней до следующего ТО"""
        if not self.next_maintenance_date:
            return None
        return (self.next_maintenance_date - timezone.now().date()).days

    def days_overdue(self):
        """Возвращает количество просроченных дней (положительное число)"""
        days = self.days_until_maintenance()
        if days is None or days >= 0:
            return 0
        return abs(days)

    class Meta:
        verbose_name = "ТО оборудования"
        verbose_name_plural = "ТО оборудования"
        app_label = 'deadline_control'
        ordering = ['equipment_name']
