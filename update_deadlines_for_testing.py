# update_deadlines_for_testing.py
"""Скрипт для обновления сроков тестовых данных - создаем просроченные и приближающиеся"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from deadline_control.models import Equipment, KeyDeadlineItem
from deadline_control.models.medical_norm import EmployeeMedicalExamination
from directory.models import Organization
from django.utils import timezone
from datetime import timedelta

org = Organization.objects.get(id=3)
print(f"Updating test data for: {org.full_name_ru}\n")

# Обновляем оборудование
print("=== UPDATING EQUIPMENT ===")
equipment = list(Equipment.objects.filter(organization=org))

for idx, eq in enumerate(equipment):
    if idx < 2:
        # Просроченные: ТО было period+1 месяц назад
        days_ago = (eq.maintenance_period_months + 1) * 30
        status = "OVERDUE"
    elif idx < 4:
        # Скоро истекает: ТО было period месяцев назад минус 5 дней
        days_ago = eq.maintenance_period_months * 30 - 5
        status = "UPCOMING"
    else:
        # Нормальный срок: ТО было месяц назад
        days_ago = 30
        status = "OK"

    maintenance_date = timezone.now().date() - timedelta(days=days_ago)
    eq.update_maintenance(new_date=maintenance_date, comment=f'Test data: {status}')
    print(f"  [{status}] {eq.equipment_name}: next ТО = {eq.next_maintenance_date}")

# Обновляем ключевые сроки
print("\n=== UPDATING KEY DEADLINES ===")
deadlines_config = [
    (-30, "OVERDUE"),  # Просрочено на 30 дней
    (-365+10, "UPCOMING"),  # Скоро истекает (через 10 дней)
    (-30, "OK"),  # Нормальный срок
]

deadlines = list(KeyDeadlineItem.objects.filter(category__organization=org))
for idx, (item, (days_offset, status)) in enumerate(zip(deadlines, deadlines_config)):
    item.current_date = timezone.now().date() + timedelta(days=days_offset)
    item.save()  # save() автоматически пересчитывает next_date
    print(f"  [{status}] {item.name}: next date = {item.next_date}")

# Обновляем медосмотры
print("\n=== UPDATING MEDICAL EXAMINATIONS ===")
medical_scenarios = {
    'Семенов Семен Семенович': (13*30, "OVERDUE"),  # Просрочен
    'Дмитриев Дмитрий Дмитриевич': (int(11.5*30), "UPCOMING"),  # Скоро истекает
    'Кузнецов Кузьма Кузьмич': (60, "OK"),  # Нормальный срок
}

for exam in EmployeeMedicalExamination.objects.filter(employee__organization=org):
    emp_name = exam.employee.full_name_nominative

    if emp_name in medical_scenarios:
        days_ago, status = medical_scenarios[emp_name]
        exam_date = timezone.now().date() - timedelta(days=days_ago)
        exam.perform_examination(examination_date=exam_date)
        print(f"  [{status}] {emp_name} - {exam.harmful_factor.short_name}: next = {exam.next_date}")
    elif not exam.date_completed:
        print(f"  [TO_ISSUE] {emp_name} - {exam.harmful_factor.short_name}: needs referral")

print("\n" + "="*60)
print("DONE! Test data updated with overdue and upcoming deadlines.")
print("="*60)
