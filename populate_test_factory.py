# populate_test_factory.py
"""Скрипт для наполнения Тестового Завода данными"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from directory.models import Organization, StructuralSubdivision, Department, Position, Employee, Commission, CommissionMember
from deadline_control.models import Equipment, KeyDeadlineCategory, KeyDeadlineItem
from deadline_control.models.medical_examination import HarmfulFactor
from deadline_control.models.medical_norm import EmployeeMedicalExamination
from directory.models.siz import SIZ, SIZNorm
from datetime import date
from django.utils import timezone
from datetime import timedelta

print("Начало создания тестовых данных...")

# Получаем Тестовый Завод
org = Organization.objects.get(id=3)
print(f"Организация: {org.full_name_ru}")

# Получаем подразделения
prod_subdivision = StructuralSubdivision.objects.filter(organization=org, name__icontains='Производственный').first()
admin_subdivision = StructuralSubdivision.objects.filter(organization=org, name__icontains='Административный').first()
assembly_dept = Department.objects.filter(subdivision=prod_subdivision, name__icontains='сборки').first() if prod_subdivision else None
painting_dept = Department.objects.filter(subdivision=prod_subdivision, name__icontains='покраски').first() if prod_subdivision else None

# Получаем должности
positions = {}
for pos in Position.objects.filter(organization=org):
    positions[pos.position_name] = pos

print(f"\nНайдено должностей: {len(positions)}")

# Создаем сотрудников
print("\n=== СОЗДАНИЕ СОТРУДНИКОВ ===")
employees_data = [
    ('Петров Петр Петрович', 'Директор завода', org, None, None, date(1975, 3, 15)),
    ('Сидоров Сидор Сидорович', 'Главный инженер', org, None, None, date(1978, 7, 22)),
    ('Кузнецов Кузьма Кузьмич', 'Начальник производственного цеха', org, prod_subdivision, None, date(1980, 5, 10)),
    ('Белов Борис Борисович', 'Инженер по охране труда', org, prod_subdivision, None, date(1985, 11, 3)),
    ('Николаев Николай Николаевич', 'Мастер участка сборки', org, prod_subdivision, assembly_dept, date(1982, 9, 8)),
    ('Семенов Семен Семенович', 'Слесарь-сборщик', org, prod_subdivision, assembly_dept, date(1990, 2, 14)),
    ('Васильев Василий Васильевич', 'Слесарь-сборщик', org, prod_subdivision, assembly_dept, date(1988, 6, 25)),
    ('Михайлов Михаил Михайлович', 'Контролер ОТК', org, prod_subdivision, assembly_dept, date(1992, 4, 17)),
    ('Алексеев Алексей Алексеевич', 'Мастер участка покраски', org, prod_subdivision, painting_dept, date(1983, 8, 20)),
    ('Дмитриев Дмитрий Дмитриевич', 'Маляр', org, prod_subdivision, painting_dept, date(1991, 1, 12)),
    ('Андреев Андрей Андреевич', 'Маляр', org, prod_subdivision, painting_dept, date(1989, 10, 5)),
    ('Федорова Федора Федоровна', 'Бухгалтер', org, admin_subdivision, None, date(1987, 12, 8)),
    ('Егорова Елена Егоровна', 'Менеджер по кадрам', org, admin_subdivision, None, date(1993, 3, 30)),
]

created_employees = {}
for name, pos_name, o, s, d, dob in employees_data:
    position = positions.get(pos_name)
    if not position:
        print(f"Пропущен: {name} - должность {pos_name} не найдена")
        continue

    emp, created = Employee.objects.get_or_create(
        full_name_nominative=name,
        organization=o,
        defaults={
            'position': position,
            'subdivision': s,
            'department': d,
            'date_of_birth': dob,
            'status': 'working',
            'height': '170-175',
            'clothing_size': '48-50',
            'shoe_size': '42'
        }
    )
    created_employees[name] = emp
    print(f"  {name}: {'создан' if created else 'существует'}")

# Создаем оборудование
print("\n=== СОЗДАНИЕ ОБОРУДОВАНИЯ ===")
equipment_data = [
    ('Компрессорная станция', org, None, None, '10000001', 12),
    ('Кран-балка 5т', org, prod_subdivision, None, '10000002', 12),
    ('Пресс гидравлический ПГ-100', org, prod_subdivision, assembly_dept, '10000003', 6),
    ('Станок сверлильный 2Н135', org, prod_subdivision, assembly_dept, '10000004', 12),
    ('Станок токарный 16К20', org, prod_subdivision, assembly_dept, '10000005', 12),
    ('Покрасочная камера КП-1', org, prod_subdivision, painting_dept, '10000006', 3),
    ('Компрессор воздушный КВ-50', org, prod_subdivision, painting_dept, '10000007', 6),
]

for idx, (name, o, s, d, inv, period) in enumerate(equipment_data):
    eq, created = Equipment.objects.get_or_create(
        inventory_number=inv,
        defaults={
            'equipment_name': name,
            'organization': o,
            'subdivision': s,
            'department': d,
            'maintenance_period_months': period,
        }
    )
    # Устанавливаем дату последнего ТО через метод update_maintenance
    if created or not eq.next_maintenance_date:
        # Создаем разные сценарии:
        # - первые 2: просроченные (ТО было давно)
        # - следующие 2: скоро истекает срок (ТО было недавно, но период короткий)
        # - остальные: нормальный срок
        if idx < 2:
            # Просроченные: ТО было period+1 месяц назад
            days_ago = (period + 1) * 30
        elif idx < 4:
            # Скоро истекает: ТО было period месяцев назад минус 5 дней
            days_ago = period * 30 - 5
        else:
            # Нормальный срок: ТО было месяц назад
            days_ago = 30

        maintenance_date = timezone.now().date() - timedelta(days=days_ago)
        eq.update_maintenance(new_date=maintenance_date, comment='Тестовые данные')
    print(f"  {name}: {'создано' if created else 'обновлено'}")

# Создаем ключевые сроки
print("\n=== СОЗДАНИЕ КЛЮЧЕВЫХ СРОКОВ ===")
category, created = KeyDeadlineCategory.objects.get_or_create(
    name='Производственные мероприятия',
    organization=org,
    defaults={
        'description': 'Плановые мероприятия производственного цеха',
        'is_active': True
    }
)
print(f"  Категория: {'создана' if created else 'существует'}")

deadlines = [
    ('Инструктаж по охране труда', 6, 'Белов Б.Б.', -30),  # Просрочено на 30 дней
    ('Проверка заземления оборудования', 12, 'Сидоров С.С.', -365+10),  # Скоро истекает (через 10 дней)
    ('Аттестация рабочих мест', 36, 'Белов Б.Б.', -30),  # Нормальный срок (было месяц назад)
]

for name, period, resp, days_offset in deadlines:
    item, created = KeyDeadlineItem.objects.get_or_create(
        category=category,
        name=name,
        defaults={
            'periodicity_months': period,
            'current_date': timezone.now().date() + timedelta(days=days_offset),
            'responsible_person': resp
        }
    )
    if not created and item.current_date != timezone.now().date() + timedelta(days=days_offset):
        # Обновляем текущую дату если элемент уже существует
        item.current_date = timezone.now().date() + timedelta(days=days_offset)
        item.save()
    print(f"  {name}: {'создано' if created else 'обновлено'} (next: {item.next_date})")

# Создаем СИЗ
print("\n=== СОЗДАНИЕ СИЗ ===")
siz_data = [
    ('Каска защитная', 'head_protection', 1, 24),
    ('Перчатки х/б', 'hand_protection', 12, 1),
    ('Респиратор', 'respiratory_protection', 1, 3),
    ('Очки защитные', 'eye_protection', 1, 12),
    ('Костюм рабочий', 'body_protection', 1, 12),
]

created_siz = {}
for name, siz_type, qty, period in siz_data:
    siz_obj, created = SIZ.objects.get_or_create(
        name=name,
        defaults={
            'classification': siz_type,
            'wear_period': period
        }
    )
    created_siz[name] = siz_obj
    print(f"  {name}: {'создан' if created else 'существует'}")

# Создаем нормы СИЗ
print("\n=== СОЗДАНИЕ НОРМ ВЫДАЧИ СИЗ ===")
slesar_position = positions.get('Слесарь-сборщик')
if slesar_position:
    for siz_name in ['Каска защитная', 'Перчатки х/б', 'Очки защитные', 'Костюм рабочий']:
        siz_obj = created_siz.get(siz_name)
        if siz_obj:
            norm, created = SIZNorm.objects.get_or_create(
                position=slesar_position,
                siz=siz_obj,
                defaults={'quantity': 1}
            )
            print(f"  Слесарь-сборщик - {siz_name}: {'создана' if created else 'существует'}")

malar_position = positions.get('Маляр')
if malar_position:
    for siz_name in ['Каска защитная', 'Перчатки х/б', 'Респиратор', 'Очки защитные', 'Костюм рабочий']:
        siz_obj = created_siz.get(siz_name)
        if siz_obj:
            norm, created = SIZNorm.objects.get_or_create(
                position=malar_position,
                siz=siz_obj,
                defaults={'quantity': 1}
            )
            print(f"  Маляр - {siz_name}: {'создана' if created else 'существует'}")

# Создаем комиссию
print("\n=== СОЗДАНИЕ КОМИССИИ ===")
commission, created = Commission.objects.get_or_create(
    name='Комиссия по охране труда',
    organization=org,
    defaults={
        'commission_type': 'safety',
        'is_active': True
    }
)
print(f"  Комиссия: {'создана' if created else 'существует'}")

# Добавляем членов
members_data = [
    ('Петров Петр Петрович', 'chairman'),
    ('Сидоров Сидор Сидорович', 'member'),
    ('Белов Борис Борисович', 'secretary'),
]

for emp_name, role in members_data:
    emp = created_employees.get(emp_name)
    if emp:
        member, created = CommissionMember.objects.get_or_create(
            commission=commission,
            employee=emp,
            defaults={'role': role}
        )
        print(f"  {emp_name}: {'добавлен' if created else 'существует'}")

# Создаем вредные факторы
print("\n=== СОЗДАНИЕ ВРЕДНЫХ ФАКТОРОВ ===")
harmful_factors_data = [
    ('ФП', 'Физические перегрузки', 12),
    ('ХФ', 'Химический фактор (краски и растворители)', 12),
    ('ШВ', 'Шум и вибрация', 12),
    ('РВ', 'Работа на высоте', 12),
]

created_factors = {}
for short, full, period in harmful_factors_data:
    factor, created = HarmfulFactor.objects.get_or_create(
        short_name=short,
        defaults={
            'full_name': full,
            'periodicity': period
        }
    )
    created_factors[full] = factor
    print(f"  {full}: {'создан' if created else 'существует'}")

# Создаем медосмотры для сотрудников
print("\n=== СОЗДАНИЕ МЕДОСМОТРОВ ===")
medical_data = [
    # Слесари должны проходить медосмотр по физическим перегрузкам и шуму
    ('Семенов Семен Семенович', ['Физические перегрузки', 'Шум и вибрация']),
    ('Васильев Василий Васильевич', ['Физические перегрузки', 'Шум и вибрация']),
    # Маляры - по химическому фактору
    ('Дмитриев Дмитрий Дмитриевич', ['Химический фактор (краски и растворители)']),
    ('Андреев Андрей Андреевич', ['Химический фактор (краски и растворители)']),
    # Начальник производства - по шуму и работе на высоте
    ('Кузнецов Кузьма Кузьмич', ['Шум и вибрация', 'Работа на высоте']),
]

for emp_name, factors in medical_data:
    emp = created_employees.get(emp_name)
    if not emp:
        continue

    for factor_name in factors:
        factor = created_factors.get(factor_name)
        if not factor:
            continue

        exam, created = EmployeeMedicalExamination.objects.get_or_create(
            employee=emp,
            harmful_factor=factor,
            defaults={
                'date_completed': None,
                'next_date': None,
                'status': 'to_issue'
            }
        )
        # Устанавливаем разные сценарии для медосмотров
        # Семенов - просрочен (медосмотр был 13 месяцев назад)
        # Дмитриев - скоро истекает (медосмотр был 11.5 месяцев назад)
        # Кузнецов - нормальный срок (медосмотр был 2 месяца назад)
        # Остальные - требуют направления
        if (created or not exam.date_completed) and emp_name == 'Семенов Семен Семенович':
            exam_date = timezone.now().date() - timedelta(days=13*30)
            exam.perform_examination(examination_date=exam_date)
            print(f"  {emp_name[:20]:20s} - {factor_name[:30]:30s}: просрочен (next: {exam.next_date})")
        elif (created or not exam.date_completed) and emp_name == 'Дмитриев Дмитрий Дмитриевич':
            exam_date = timezone.now().date() - timedelta(days=int(11.5*30))
            exam.perform_examination(examination_date=exam_date)
            print(f"  {emp_name[:20]:20s} - {factor_name[:30]:30s}: скоро истекает (next: {exam.next_date})")
        elif (created or not exam.date_completed) and emp_name == 'Кузнецов Кузьма Кузьмич':
            exam_date = timezone.now().date() - timedelta(days=60)
            exam.perform_examination(examination_date=exam_date)
            print(f"  {emp_name[:20]:20s} - {factor_name[:30]:30s}: нормальный срок (next: {exam.next_date})")
        else:
            print(f"  {emp_name[:20]:20s} - {factor_name[:30]:30s}: требуется направление")

# Статистика
print("\n" + "="*60)
print("ИТОГОВАЯ СТАТИСТИКА:")
print("="*60)
print(f"  Должности: {Position.objects.filter(organization=org).count()}")
print(f"  Сотрудники: {Employee.objects.filter(organization=org).count()}")
print(f"  Оборудование: {Equipment.objects.filter(organization=org).count()}")
print(f"  Категории сроков: {KeyDeadlineCategory.objects.filter(organization=org).count()}")
print(f"  Мероприятия: {KeyDeadlineItem.objects.filter(category__organization=org).count()}")
print(f"  СИЗ (всего): {SIZ.objects.count()}")
print(f"  Нормы СИЗ: {SIZNorm.objects.filter(position__organization=org).count()}")
print(f"  Комиссии: {Commission.objects.filter(organization=org).count()}")
print(f"  Члены комиссий: {CommissionMember.objects.filter(commission__organization=org).count()}")
print(f"  Вредные факторы (всего): {HarmfulFactor.objects.count()}")
print(f"  Медосмотры: {EmployeeMedicalExamination.objects.filter(employee__organization=org).count()}")
print("="*60)
print("ГОТОВО! Тестовый Завод заполнен данными.")
