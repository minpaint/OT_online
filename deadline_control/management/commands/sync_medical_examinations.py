# deadline_control/management/commands/sync_medical_examinations.py

from django.core.management.base import BaseCommand
from directory.models import Employee
from directory.signals import get_harmful_factors_for_position
from deadline_control.models import EmployeeMedicalExamination


class Command(BaseCommand):
    help = 'Создает недостающие записи медосмотров для всех сотрудников'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать что будет создано, но не создавать записи',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('Режим проверки (dry-run) - записи не будут созданы'))
        else:
            self.stdout.write(self.style.SUCCESS('Создание недостающих записей медосмотров...'))

        total_employees = 0
        total_created = 0
        employees_without_position = 0

        # Получаем всех активных сотрудников
        employees = Employee.objects.exclude(
            status__in=['candidate', 'fired']
        ).select_related('position').prefetch_related(
            'medical_examinations',
            'position__medical_factors__harmful_factor'
        )

        for employee in employees:
            total_employees += 1

            if not employee.position:
                employees_without_position += 1
                continue

            # Получаем вредные факторы для должности с учетом иерархии
            harmful_factors = get_harmful_factors_for_position(employee.position)

            if not harmful_factors.exists():
                continue

            # Получаем существующие медосмотры
            existing_factor_ids = set(
                employee.medical_examinations.values_list('harmful_factor_id', flat=True)
            )

            # Создаем недостающие записи
            for factor in harmful_factors:
                if factor.id not in existing_factor_ids:
                    if not dry_run:
                        EmployeeMedicalExamination.objects.create(
                            employee=employee,
                            harmful_factor=factor,
                        )
                        self.stdout.write(
                            f'  [OK] Создан медосмотр: {employee.full_name_nominative} -> {factor.short_name}'
                        )
                    else:
                        self.stdout.write(
                            f'  [PLAN] Будет создан: {employee.full_name_nominative} -> {factor.short_name}'
                        )
                    total_created += 1

        # Итоги
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f'Обработано сотрудников: {total_employees}')
        self.stdout.write(f'Без должности: {employees_without_position}')

        if dry_run:
            self.stdout.write(f'Будет создано записей: {total_created}')
        else:
            self.stdout.write(f'Создано записей: {total_created}')

        self.stdout.write(self.style.SUCCESS('=' * 60))
