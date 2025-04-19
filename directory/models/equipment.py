# directory/models/equipment.py
from django.db import models
from django.utils import timezone
from datetime import timedelta
import json


class Equipment(models.Model):
    """
    ⚙️ Модель для хранения оборудования.
    Оборудование привязано к организации, подразделению и отделу.
    Содержит информацию о техническом обслуживании.
    """
    equipment_name = models.CharField("Наименование оборудования", max_length=255)
    inventory_number = models.CharField("Инвентарный номер", max_length=100, unique=True)
    organization = models.ForeignKey(
        'directory.Organization',
        on_delete=models.CASCADE,
        related_name="equipment",
        verbose_name="Организация"
    )
    subdivision = models.ForeignKey(
        'directory.StructuralSubdivision',
        on_delete=models.CASCADE,
        verbose_name="Структурное подразделение",
        null=True,
        blank=True
    )
    department = models.ForeignKey(
        'directory.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Отдел"
    )

    # Поля для технического обслуживания
    last_maintenance_date = models.DateField("Дата последнего ТО", null=True, blank=True)
    next_maintenance_date = models.DateField("Дата следующего ТО", null=True, blank=True)
    maintenance_period_days = models.PositiveIntegerField("Периодичность ТО (дней)", default=365)
    maintenance_history = models.JSONField("История ТО", default=list, blank=True)

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

    def update_maintenance(self, new_date=None):
        """
        Обновляет информацию о ТО оборудования.
        Если дата не указана, используется текущая.
        """
        # Если дата не передана, используем текущую
        maintenance_date = new_date or timezone.now().date()

        # Если была предыдущая дата ТО, добавляем её в историю
        if self.last_maintenance_date:
            # Преобразуем в список, если поле было None или пустым
            history = self.maintenance_history if isinstance(self.maintenance_history, list) else []
            # Добавляем дату в формате ISO (YYYY-MM-DD)
            history.append(self.last_maintenance_date.isoformat())
            # Ограничиваем историю 10 последними записями
            self.maintenance_history = history[-10:]

        # Обновляем даты
        self.last_maintenance_date = maintenance_date

        # Вычисляем дату следующего ТО
        self.next_maintenance_date = maintenance_date + timedelta(days=self.maintenance_period_days)

        # Обновляем статус
        self.maintenance_status = 'operational'

        self.save()

    def is_maintenance_required(self):
        """Проверяет, требуется ли оборудованию ТО"""
        today = timezone.now().date()

        # Если дата следующего ТО установлена и она уже прошла или наступает в следующие 7 дней
        if self.next_maintenance_date and self.next_maintenance_date <= (today + timedelta(days=7)):
            return True
        return False

    def days_until_maintenance(self):
        """Возвращает количество дней до следующего ТО"""
        if not self.next_maintenance_date:
            return None

        today = timezone.now().date()
        delta = self.next_maintenance_date - today
        return delta.days

    class Meta:
        verbose_name = "Оборудование"
        verbose_name_plural = "Оборудование"