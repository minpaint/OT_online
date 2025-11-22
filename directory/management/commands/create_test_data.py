# directory/management/commands/create_test_data.py
"""
Management команда для создания тестовых данных в Тестовом Заводе
для проверки системы прав доступа
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal

from directory.models import (
    Organization,
    StructuralSubdivision,
    Department,
    Position,
    Employee,
    Commission,
    CommissionMember
)
from directory.models.siz import SIZ, SIZNorm
from deadline_control.models import Equipment, KeyDeadlineCategory, KeyDeadlineItem
from deadline_control.models.medical_norm import (
    MedicalExaminationType,
    HarmfulFactor,
    PositionMedicalFactor,
    EmployeeMedicalExamination
)


class Command(BaseCommand):
    help = 'Создает тестовые данные для Тестового Завода'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Начало создания тестовых данных...'))

        # Получаем Тестовый Завод
        try:
            org = Organization.objects.get(id=3)
            self.stdout.write(f'Организация: {org.full_name_ru}')
        except Organization.DoesNotExist:
            self.stdout.write(self.style.ERROR('Тестовый Завод не найден!'))
            return

        # Получаем подразделения и отделы
        prod_subdivision = StructuralSubdivision.objects.filter(
            organization=org, name__icontains='Производственный'
        ).first()
        admin_subdivision = StructuralSubdivision.objects.filter(
            organization=org, name__icontains='Административный'
        ).first()

        assembly_dept = None
        painting_dept = None
        if prod_subdivision:
            assembly_dept = Department.objects.filter(
                subdivision=prod_subdivision, name__icontains='сборки'
            ).first()
            painting_dept = Department.objects.filter(
                subdivision=prod_subdivision, name__icontains='покраски'
            ).first()

        self.stdout.write('\n=== СОЗДАНИЕ ДОЛЖНОСТЕЙ ===')
        positions_data = [
            # Организация (без подразделения)
            {
                'organization': org,
                'subdivision': None,
                'department': None,
                'position_name': 'Директор завода',
            },
            {
                'organization': org,
                'subdivision': None,
                'department': None,
                'position_name': 'Главный инженер',
            },
            # Производственный цех
            {
                'organization': org,
                'subdivision': prod_subdivision,
                'department': None,
                'position_name': 'Начальник производственного цеха',
            },
            {
                'organization': org,
                'subdivision': prod_subdivision,
                'department': None,
                'position_name': 'Инженер по охране труда',
            },
            # Участок сборки
            {
                'organization': org,
                'subdivision': prod_subdivision,
                'department': assembly_dept,
                'position_name': 'Мастер участка сборки',
            },
            {
                'organization': org,
                'subdivision': prod_subdivision,
                'department': assembly_dept,
                'position_name': 'Слесарь-сборщик',
            },
            {
                'organization': org,
                'subdivision': prod_subdivision,
                'department': assembly_dept,
                'position_name': 'Контролер ОТК',
            },
            # Участок покраски
            {
                'organization': org,
                'subdivision': prod_subdivision,
                'department': painting_dept,
                'position_name': 'Мастер участка покраски',
            },
            {
                'organization': org,
                'subdivision': prod_subdivision,
                'department': painting_dept,
                'position_name': 'Маляр',
            },
            # Административный отдел
            {
                'organization': org,
                'subdivision': admin_subdivision,
                'department': None,
                'position_name': 'Бухгалтер',
            },
            {
                'organization': org,
                'subdivision': admin_subdivision,
                'department': None,
                'position_name': 'Менеджер по кадрам',
            },
        ]

        created_positions = {}
        for pos_data in positions_data:
            if pos_data['subdivision'] is None:
                # Должности на уровне организации
                position, created = Position.objects.get_or_create(
                    organization=pos_data['organization'],
                    position_name=pos_data['position_name'],
                    subdivision__isnull=True,
                    department__isnull=True
                )
            elif pos_data['department']:
                # Должности на уровне отдела
                position, created = Position.objects.get_or_create(
                    organization=pos_data['organization'],
                    subdivision=pos_data['subdivision'],
                    department=pos_data['department'],
                    position_name=pos_data['position_name']
                )
            else:
                # Должности на уровне подразделения
                position, created = Position.objects.get_or_create(
                    organization=pos_data['organization'],
                    subdivision=pos_data['subdivision'],
                    position_name=pos_data['position_name'],
                    department__isnull=True
                )

            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Создана должность: {position.position_name}'))
            else:
                self.stdout.write(f'  • Должность уже существует: {position.position_name}')

            created_positions[pos_data['position_name']] = position

        self.stdout.write('\n=== СОЗДАНИЕ СОТРУДНИКОВ ===')
        employees_data = [
            # Организация
            {
                'full_name': 'Петров Петр Петрович',
                'position': 'Директор завода',
                'organization': org,
                'subdivision': None,
                'department': None,
                'date_of_birth': date(1975, 3, 15),
                'status': 'working'
            },
            {
                'full_name': 'Сидоров Сидор Сидорович',
                'position': 'Главный инженер',
                'organization': org,
                'subdivision': None,
                'department': None,
                'date_of_birth': date(1978, 7, 22),
                'status': 'working'
            },
            # Производственный цех
            {
                'full_name': 'Кузнецов Кузьма Кузьмич',
                'position': 'Начальник производственного цеха',
                'organization': org,
                'subdivision': prod_subdivision,
                'department': None,
                'date_of_birth': date(1980, 5, 10),
                'status': 'working'
            },
            {
                'full_name': 'Белов Борис Борисович',
                'position': 'Инженер по охране труда',
                'organization': org,
                'subdivision': prod_subdivision,
                'department': None,
                'date_of_birth': date(1985, 11, 3),
                'status': 'working'
            },
            # Участок сборки
            {
                'full_name': 'Николаев Николай Николаевич',
                'position': 'Мастер участка сборки',
                'organization': org,
                'subdivision': prod_subdivision,
                'department': assembly_dept,
                'date_of_birth': date(1982, 9, 8),
                'status': 'working'
            },
            {
                'full_name': 'Семенов Семен Семенович',
                'position': 'Слесарь-сборщик',
                'organization': org,
                'subdivision': prod_subdivision,
                'department': assembly_dept,
                'date_of_birth': date(1990, 2, 14),
                'status': 'working'
            },
            {
                'full_name': 'Васильев Василий Васильевич',
                'position': 'Слесарь-сборщик',
                'organization': org,
                'subdivision': prod_subdivision,
                'department': assembly_dept,
                'date_of_birth': date(1988, 6, 25),
                'status': 'working'
            },
            {
                'full_name': 'Михайлов Михаил Михайлович',
                'position': 'Контролер ОТК',
                'organization': org,
                'subdivision': prod_subdivision,
                'department': assembly_dept,
                'date_of_birth': date(1992, 4, 17),
                'status': 'working'
            },
            # Участок покраски
            {
                'full_name': 'Алексеев Алексей Алексеевич',
                'position': 'Мастер участка покраски',
                'organization': org,
                'subdivision': prod_subdivision,
                'department': painting_dept,
                'date_of_birth': date(1983, 8, 20),
                'status': 'working'
            },
            {
                'full_name': 'Дмитриев Дмитрий Дмитриевич',
                'position': 'Маляр',
                'organization': org,
                'subdivision': prod_subdivision,
                'department': painting_dept,
                'date_of_birth': date(1991, 1, 12),
                'status': 'working'
            },
            {
                'full_name': 'Андреев Андрей Андреевич',
                'position': 'Маляр',
                'organization': org,
                'subdivision': prod_subdivision,
                'department': painting_dept,
                'date_of_birth': date(1989, 10, 5),
                'status': 'working'
            },
            # Административный отдел
            {
                'full_name': 'Федорова Федора Федоровна',
                'position': 'Бухгалтер',
                'organization': org,
                'subdivision': admin_subdivision,
                'department': None,
                'date_of_birth': date(1987, 12, 8),
                'status': 'working'
            },
            {
                'full_name': 'Егорова Елена Егоровна',
                'position': 'Менеджер по кадрам',
                'organization': org,
                'subdivision': admin_subdivision,
                'department': None,
                'date_of_birth': date(1993, 3, 30),
                'status': 'working'
            },
        ]

        created_employees = {}
        for emp_data in employees_data:
            position = created_positions.get(emp_data['position'])
            if not position:
                self.stdout.write(self.style.WARNING(f'  ⚠ Должность не найдена: {emp_data["position"]}'))
                continue

            employee, created = Employee.objects.get_or_create(
                full_name_nominative=emp_data['full_name'],
                organization=emp_data['organization'],
                defaults={
                    'position': position,
                    'subdivision': emp_data['subdivision'],
                    'department': emp_data['department'],
                    'date_of_birth': emp_data['date_of_birth'],
                    'status': emp_data['status'],
                    'height': '170-175',
                    'clothing_size': '48-50',
                    'shoe_size': '42'
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Создан сотрудник: {employee.full_name_nominative}'))
            else:
                self.stdout.write(f'  • Сотрудник уже существует: {employee.full_name_nominative}')

            created_employees[emp_data['full_name']] = employee

        self.stdout.write('\n=== СОЗДАНИЕ ОБОРУДОВАНИЯ ===')
        equipment_data = [
            # Организация
            {
                'name': 'Компрессорная станция',
                'organization': org,
                'subdivision': None,
                'department': None,
                'inventory_number': '00000001',
                'periodicity_months': 12
            },
            # Производственный цех
            {
                'name': 'Кран-балка 5т',
                'organization': org,
                'subdivision': prod_subdivision,
                'department': None,
                'inventory_number': '00000002',
                'periodicity_months': 12
            },
            # Участок сборки
            {
                'name': 'Пресс гидравлический ПГ-100',
                'organization': org,
                'subdivision': prod_subdivision,
                'department': assembly_dept,
                'inventory_number': '00000003',
                'periodicity_months': 6
            },
            {
                'name': 'Станок сверлильный 2Н135',
                'organization': org,
                'subdivision': prod_subdivision,
                'department': assembly_dept,
                'inventory_number': '00000004',
                'periodicity_months': 12
            },
            {
                'name': 'Станок токарный 16К20',
                'organization': org,
                'subdivision': prod_subdivision,
                'department': assembly_dept,
                'inventory_number': '00000005',
                'periodicity_months': 12
            },
            # Участок покраски
            {
                'name': 'Покрасочная камера КП-1',
                'organization': org,
                'subdivision': prod_subdivision,
                'department': painting_dept,
                'inventory_number': '00000006',
                'periodicity_months': 3
            },
            {
                'name': 'Компрессор воздушный КВ-50',
                'organization': org,
                'subdivision': prod_subdivision,
                'department': painting_dept,
                'inventory_number': '00000007',
                'periodicity_months': 6
            },
        ]

        for eq_data in equipment_data:
            equipment, created = Equipment.objects.get_or_create(
                inventory_number=eq_data['inventory_number'],
                defaults={
                    'equipment_name': eq_data['name'],
                    'organization': eq_data['organization'],
                    'subdivision': eq_data['subdivision'],
                    'department': eq_data['department'],
                    'maintenance_periodicity_months': eq_data['periodicity_months'],
                    'last_maintenance_date': timezone.now().date() - timedelta(days=30),
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Создано оборудование: {equipment.equipment_name}'))
            else:
                self.stdout.write(f'  • Оборудование уже существует: {equipment.equipment_name}')

        self.stdout.write('\n=== СОЗДАНИЕ КЛЮЧЕВЫХ СРОКОВ ===')
        category, created = KeyDeadlineCategory.objects.get_or_create(
            name='Производственные мероприятия',
            organization=org,
            defaults={
                'description': 'Плановые мероприятия производственного цеха',
                'is_active': True
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'  ✓ Создана категория: {category.name}'))
        else:
            self.stdout.write(f'  • Категория уже существует: {category.name}')

        deadlines_data = [
            {
                'name': 'Инструктаж по охране труда',
                'periodicity': 6,
                'responsible': 'Белов Б.Б.'
            },
            {
                'name': 'Проверка заземления оборудования',
                'periodicity': 12,
                'responsible': 'Сидоров С.С.'
            },
            {
                'name': 'Аттестация рабочих мест',
                'periodicity': 36,
                'responsible': 'Белов Б.Б.'
            },
        ]

        for dl_data in deadlines_data:
            item, created = KeyDeadlineItem.objects.get_or_create(
                category=category,
                name=dl_data['name'],
                defaults={
                    'periodicity_months': dl_data['periodicity'],
                    'current_date': timezone.now().date(),
                    'responsible_person': dl_data['responsible']
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Создано мероприятие: {item.name}'))
            else:
                self.stdout.write(f'  • Мероприятие уже существует: {item.name}')

        self.stdout.write('\n=== СОЗДАНИЕ СИЗ ===')
        siz_data = [
            {
                'name': 'Каска защитная',
                'type': 'head_protection',
                'norm_issue': 1,
                'norm_period': 24
            },
            {
                'name': 'Перчатки х/б',
                'type': 'hand_protection',
                'norm_issue': 12,
                'norm_period': 1
            },
            {
                'name': 'Респиратор',
                'type': 'respiratory_protection',
                'norm_issue': 1,
                'norm_period': 3
            },
            {
                'name': 'Очки защитные',
                'type': 'eye_protection',
                'norm_issue': 1,
                'norm_period': 12
            },
            {
                'name': 'Костюм рабочий',
                'type': 'body_protection',
                'norm_issue': 1,
                'norm_period': 12
            },
        ]

        created_siz = {}
        for siz in siz_data:
            siz_obj, created = SIZ.objects.get_or_create(
                name=siz['name'],
                organization=org,
                defaults={
                    'siz_type': siz['type'],
                    'norm_issue_quantity': siz['norm_issue'],
                    'norm_period_months': siz['norm_period']
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Создан СИЗ: {siz_obj.name}'))
            else:
                self.stdout.write(f'  • СИЗ уже существует: {siz_obj.name}')

            created_siz[siz['name']] = siz_obj

        # Создаем нормы СИЗ для должностей
        self.stdout.write('\n=== СОЗДАНИЕ НОРМ ВЫДАЧИ СИЗ ===')

        # Слесарь-сборщик
        slesar_position = created_positions.get('Слесарь-сборщик')
        if slesar_position:
            for siz_name in ['Каска защитная', 'Перчатки х/б', 'Очки защитные', 'Костюм рабочий']:
                siz_obj = created_siz.get(siz_name)
                if siz_obj:
                    norm, created = SIZNorm.objects.get_or_create(
                        position=slesar_position,
                        siz=siz_obj,
                        defaults={
                            'quantity': siz_obj.norm_issue_quantity,
                            'period_months': siz_obj.norm_period_months
                        }
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(f'  ✓ Норма СИЗ: {slesar_position.position_name} - {siz_obj.name}'))

        # Маляр
        malar_position = created_positions.get('Маляр')
        if malar_position:
            for siz_name in ['Каска защитная', 'Перчатки х/б', 'Респиратор', 'Очки защитные', 'Костюм рабочий']:
                siz_obj = created_siz.get(siz_name)
                if siz_obj:
                    norm, created = SIZNorm.objects.get_or_create(
                        position=malar_position,
                        siz=siz_obj,
                        defaults={
                            'quantity': siz_obj.norm_issue_quantity,
                            'period_months': siz_obj.norm_period_months
                        }
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(f'  ✓ Норма СИЗ: {malar_position.position_name} - {siz_obj.name}'))

        self.stdout.write('\n=== СОЗДАНИЕ КОМИССИИ ===')
        commission, created = Commission.objects.get_or_create(
            name='Комиссия по охране труда',
            organization=org,
            defaults={
                'commission_type': 'safety',
                'is_active': True
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'  ✓ Создана комиссия: {commission.name}'))
        else:
            self.stdout.write(f'  • Комиссия уже существует: {commission.name}')

        # Добавляем членов комиссии
        members_data = [
            ('Петров Петр Петрович', 'chairman'),
            ('Сидоров Сидор Сидорович', 'member'),
            ('Белов Борис Борисович', 'secretary'),
        ]

        for emp_name, role in members_data:
            employee = created_employees.get(emp_name)
            if employee:
                member, created = CommissionMember.objects.get_or_create(
                    commission=commission,
                    employee=employee,
                    defaults={'role': role}
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Добавлен член комиссии: {employee.full_name_nominative}'))

        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('✅ ТЕСТОВЫЕ ДАННЫЕ УСПЕШНО СОЗДАНЫ!'))
        self.stdout.write('='*60)

        # Статистика
        self.stdout.write('\nСТАТИСТИКА:')
        self.stdout.write(f'  Должности: {Position.objects.filter(organization=org).count()}')
        self.stdout.write(f'  Сотрудники: {Employee.objects.filter(organization=org).count()}')
        self.stdout.write(f'  Оборудование: {Equipment.objects.filter(organization=org).count()}')
        self.stdout.write(f'  Категории сроков: {KeyDeadlineCategory.objects.filter(organization=org).count()}')
        self.stdout.write(f'  Мероприятия: {KeyDeadlineItem.objects.filter(category__organization=org).count()}')
        self.stdout.write(f'  СИЗ: {SIZ.objects.filter(organization=org).count()}')
        self.stdout.write(f'  Нормы СИЗ: {SIZNorm.objects.filter(position__organization=org).count()}')
        self.stdout.write(f'  Комиссии: {Commission.objects.filter(organization=org).count()}')
        self.stdout.write(f'  Члены комиссий: {CommissionMember.objects.filter(commission__organization=org).count()}')
