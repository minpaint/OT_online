def step2_create_models(self):
    """Шаг 2: Создание моделей"""
    print("Шаг 2: Создание моделей...")

    models = {
        'organization.py': '''from django.db import models

class Organization(models.Model):
    """Справочник: Организации."""
    full_name_ru = models.CharField(max_length=255, verbose_name="Полное наименование (рус)")
    requisites_ru = models.TextField(verbose_name="Реквизиты (рус)")
    full_name_by = models.CharField(max_length=255, verbose_name="Полное наименование (бел)")
    short_name_by = models.CharField(max_length=255, verbose_name="Сокращенное наименование (бел)")
    requisites_by = models.TextField(verbose_name="Реквизиты (бел)")

    def __str__(self):
        return self.full_name_ru

    class Meta:
        verbose_name = "Организация"
        verbose_name_plural = "Организации"''',

        'subdivision.py': '''from django.db import models
from .organization import Organization

class StructuralSubdivision(models.Model):
    """Справочник: Структурные подразделения."""
    name = models.CharField(max_length=255, verbose_name="Наименование")
    short_name = models.CharField(max_length=255, blank=True, verbose_name="Сокращенное наименование")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="subdivisions", verbose_name="Организация")
    parent_subdivision = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='child_subdivisions', verbose_name="Родительское подразделение")

    def __str__(self):
        return f"{self.name} ({self.organization.full_name_ru})"

    class Meta:
        verbose_name = "Структурное подразделение"
        verbose_name_plural = "Структурные подразделения"''',

        'department.py': '''from django.db import models
from .organization import Organization
from .subdivision import StructuralSubdivision

class Department(models.Model):
    """Справочник: Отделы."""
    name = models.CharField(max_length=255, verbose_name="Наименование")
    short_name = models.CharField(max_length=255, blank=True, verbose_name="Сокращенное наименование")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="departments", verbose_name="Организация")
    subdivision = models.ForeignKey(StructuralSubdivision, on_delete=models.SET_NULL, null=True, blank=True, related_name="departments", verbose_name="Структурное подразделение")

    def __str__(self):
        return f"{self.name} ({self.organization.full_name_ru})"

    class Meta:
        verbose_name = "Отдел"
        verbose_name_plural = "Отделы"''',

        'document.py': '''from django.db import models

class Document(models.Model):
    """Справочник: Документы (реестр документов)."""
    name = models.CharField(max_length=255, verbose_name="Наименование документа")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Документ"
        verbose_name_plural = "Документы"''',

        'equipment.py': '''from django.db import models
from .organization import Organization
from .subdivision import StructuralSubdivision

class Equipment(models.Model):
    """Справочник: Оборудование."""
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="equipment", verbose_name="Организация")
    subdivision = models.ForeignKey(StructuralSubdivision, on_delete=models.SET_NULL, null=True, blank=True, related_name="equipment", verbose_name="Структурное подразделение")
    equipment_name = models.CharField(max_length=255, verbose_name="Наименование оборудования")
    inventory_number = models.CharField(max_length=100, unique=True, verbose_name="Инвентарный номер")

    def __str__(self):
        return f"{self.equipment_name} (инв.№ {self.inventory_number})"

    class Meta:
        verbose_name = "Оборудование"
        verbose_name_plural = "Оборудование"''',

        'position.py': '''from django.db import models
from .organization import Organization
from .subdivision import StructuralSubdivision
from .department import Department
from .document import Document
from .equipment import Equipment

class Position(models.Model):
    """Справочник: Профессии и должности."""
    ELECTRICAL_GROUP_CHOICES = [
        ("I", "I"),
        ("II", "II"),
        ("III", "III"),
        ("IV", "IV"),
        ("V", "V"),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="positions", verbose_name="Организация")
    subdivision = models.ForeignKey(StructuralSubdivision, on_delete=models.SET_NULL, null=True, blank=True, related_name="positions", verbose_name="Структурное подразделение")
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="positions", verbose_name="Отдел")
    position_name = models.CharField(max_length=255, verbose_name="Название")
    safety_instructions_numbers = models.CharField(max_length=255, blank=True, verbose_name="Номера инструкций по ОТ")
    electrical_safety_group = models.CharField(max_length=4, choices=ELECTRICAL_GROUP_CHOICES, blank=True, verbose_name="Группа по электробезопасности")
    internship_period_days = models.PositiveIntegerField(default=0, verbose_name="Срок стажировки (дни)")
    is_responsible_for_safety = models.BooleanField(default=False, verbose_name="Ответственный за ОТ")
    is_electrical_personnel = models.BooleanField(default=False, verbose_name="Электротехнический персонал")
    documents = models.ManyToManyField(Document, blank=True, related_name="positions", verbose_name="Документы")
    equipment = models.ManyToManyField(Equipment, blank=True, related_name="positions", verbose_name="Оборудование")

    def __str__(self):
        return self.position_name

    class Meta:
        verbose_name = "Профессия/должность"
        verbose_name_plural = "Профессии/должности"''',

        'employee.py': '''from django.db import models
from .subdivision import StructuralSubdivision
from .position import Position

class Employee(models.Model):
    """Справочник: Сотрудники."""
    HEIGHT_CHOICES = [
        ("158-164 см", "158-164 см"),
        ("170-176 см", "170-176 см"),
        ("182-188 см", "182-188 см"),
        ("194-200 см", "194-200 см"),
    ]

    CLOTHING_SIZE_CHOICES = [
        ("44-46", "44-46"),
        ("48-50", "48-50"),
        ("52-54", "52-54"),
        ("56-58", "56-58"),
        ("60-62", "60-62"),
        ("64-66", "64-66"),
    ]

    SHOE_SIZE_CHOICES = [(str(i), str(i)) for i in range(36, 49)]

    full_name_nominative = models.CharField(max_length=255, verbose_name="ФИО (именительный)")
    full_name_dative = models.CharField(max_length=255, verbose_name="ФИО (дательный)")
    date_of_birth = models.DateField(verbose_name="Дата рождения")
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True, related_name="employees", verbose_name="Должность")
    structural_subdivision = models.ForeignKey(StructuralSubdivision, on_delete=models.SET_NULL, null=True, blank=True, related_name="employees", verbose_name="Подразделение")
    place_of_residence = models.TextField(verbose_name="Место проживания")
    height = models.CharField(max_length=15, choices=HEIGHT_CHOICES, blank=True, verbose_name="Рост")
    clothing_size = models.CharField(max_length=5, choices=CLOTHING_SIZE_CHOICES, blank=True, verbose_name="Размер одежды")
    shoe_size = models.CharField(max_length=2, choices=SHOE_SIZE_CHOICES, blank=True, verbose_name="Размер обуви")
    is_contractor = models.BooleanField(default=False, verbose_name="Договор подряда")

    def __str__(self):
        return self.full_name_nominative

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"''',

        '__init__.py': '''from .organization import Organization
from .subdivision import StructuralSubdivision
from .department import Department
from .document import Document
from .equipment import Equipment
from .position import Position
from .employee import Employee

__all__ = [
    'Organization',
    'StructuralSubdivision',
    'Department',
    'Document',
    'Equipment',
    'Position',
    'Employee',
]'''
    }

    # Создаем файлы моделей
    for filename, content in models.items():
        filepath = f"{self.base_dir}/directory/models/{filename}"
        self.create_file(filepath, content)

    print("Модели созданы успешно!")