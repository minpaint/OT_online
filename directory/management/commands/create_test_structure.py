from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from directory.models import (
    Organization, StructuralSubdivision, Department,
    Position, Employee, Profile
)
from deadline_control.models import Equipment
from directory.models.siz import SIZ
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Создание тестовой организационной структуры для проверки прав доступа'

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("Создание тестовой структуры"))
        self.stdout.write("=" * 80)

        # 1. Организация
        self.stdout.write("\nШаг 1: Создание организации")
        org, created = Organization.objects.get_or_create(
            full_name_ru='Общество с ограниченной ответственностью "Тестовый Завод"',
            defaults={
                'short_name_ru': 'ООО "Тестовый Завод"',
                'full_name_by': 'Таварыства з абмежаванай адказнасцю "Тэставы Завод"',
                'short_name_by': 'ТАА "Тэставы Завод"',
                'location': 'г. Минск',
            }
        )
        self.stdout.write(f"  {'Создана' if created else 'Существует'}: {org.short_name_ru}")

        # 2. Подразделения
        self.stdout.write("\nШаг 2: Создание подразделений")

        pc1, created = StructuralSubdivision.objects.get_or_create(
            organization=org,
            name='Производственный цех №1',
            defaults={'short_name': 'Цех №1'}
        )
        self.stdout.write(f"  {'Создано' if created else 'Существует'}: {pc1.name}")

        pc2, created = StructuralSubdivision.objects.get_or_create(
            organization=org,
            name='Производственный цех №2',
            defaults={'short_name': 'Цех №2'}
        )
        self.stdout.write(f"  {'Создано' if created else 'Существует'}: {pc2.name}")

        adm, created = StructuralSubdivision.objects.get_or_create(
            organization=org,
            name='Административный корпус',
            defaults={'short_name': 'АДМ'}
        )
        self.stdout.write(f"  {'Создано' if created else 'Существует'}: {adm.name}")

        # 3. Отделы
        self.stdout.write("\nШаг 3: Создание отделов")

        # Отделы цеха 1
        us1, created = Department.objects.get_or_create(
            organization=org,
            subdivision=pc1,
            name='Участок сборки',
            defaults={'short_name': 'Сборка'}
        )
        self.stdout.write(f"  {'Создан' if created else 'Существует'}: {us1.name}")

        up1, created = Department.objects.get_or_create(
            organization=org,
            subdivision=pc1,
            name='Участок покраски',
            defaults={'short_name': 'Покраска'}
        )
        self.stdout.write(f"  {'Создан' if created else 'Существует'}: {up1.name}")

        # Отделы цеха 2
        um2, created = Department.objects.get_or_create(
            organization=org,
            subdivision=pc2,
            name='Участок механообработки',
            defaults={'short_name': 'Мехобработка'}
        )
        self.stdout.write(f"  {'Создан' if created else 'Существует'}: {um2.name}")

        usv2, created = Department.objects.get_or_create(
            organization=org,
            subdivision=pc2,
            name='Участок сварки',
            defaults={'short_name': 'Сварка'}
        )
        self.stdout.write(f"  {'Создан' if created else 'Существует'}: {usv2.name}")

        # Административные отделы
        ok, created = Department.objects.get_or_create(
            organization=org,
            subdivision=adm,
            name='Отдел кадров',
            defaults={'short_name': 'Кадры'}
        )
        self.stdout.write(f"  {'Создан' if created else 'Существует'}: {ok.name}")

        # 4. Должности
        self.stdout.write("\nШаг 4: Создание должностей")

        pos_director, _ = Position.objects.get_or_create(
            organization=org,
            subdivision=adm,
            department=ok,
            position_name='Генеральный директор'
        )

        pos_workshop1, _ = Position.objects.get_or_create(
            organization=org,
            subdivision=pc1,
            department=None,
            position_name='Начальник цеха'
        )

        pos_master1, _ = Position.objects.get_or_create(
            organization=org,
            subdivision=pc1,
            department=us1,
            position_name='Мастер участка'
        )

        pos_worker1, _ = Position.objects.get_or_create(
            organization=org,
            subdivision=pc1,
            department=us1,
            position_name='Слесарь-сборщик'
        )

        pos_worker2, _ = Position.objects.get_or_create(
            organization=org,
            subdivision=pc2,
            department=um2,
            position_name='Токарь'
        )

        self.stdout.write(f"  Создано должностей: 5")

        # 5. Сотрудники
        self.stdout.write("\nШаг 5: Создание сотрудников")

        emp1, created = Employee.objects.get_or_create(
            full_name_nominative='Петров Петр Петрович',
            defaults={
                'organization': org,
                'subdivision': adm,
                'department': ok,
                'position': pos_director,
                'hire_date': timezone.now().date() - timedelta(days=1825),
                'date_of_birth': timezone.now().date() - timedelta(days=365*45),
            }
        )
        self.stdout.write(f"  {'Создан' if created else 'Существует'}: {emp1.full_name_nominative}")

        emp2, created = Employee.objects.get_or_create(
            full_name_nominative='Сидоров Сидор Сидорович',
            defaults={
                'organization': org,
                'subdivision': pc1,
                'department': None,
                'position': pos_workshop1,
                'hire_date': timezone.now().date() - timedelta(days=1095),
                'date_of_birth': timezone.now().date() - timedelta(days=365*40),
            }
        )
        self.stdout.write(f"  {'Создан' if created else 'Существует'}: {emp2.full_name_nominative}")

        emp3, created = Employee.objects.get_or_create(
            full_name_nominative='Кузнецов Алексей Николаевич',
            defaults={
                'organization': org,
                'subdivision': pc1,
                'department': us1,
                'position': pos_master1,
                'hire_date': timezone.now().date() - timedelta(days=730),
                'date_of_birth': timezone.now().date() - timedelta(days=365*35),
            }
        )
        self.stdout.write(f"  {'Создан' if created else 'Существует'}: {emp3.full_name_nominative}")

        emp4, created = Employee.objects.get_or_create(
            full_name_nominative='Морозов Дмитрий Александрович',
            defaults={
                'organization': org,
                'subdivision': pc1,
                'department': us1,
                'position': pos_worker1,
                'hire_date': timezone.now().date() - timedelta(days=365),
                'date_of_birth': timezone.now().date() - timedelta(days=365*28),
            }
        )
        self.stdout.write(f"  {'Создан' if created else 'Существует'}: {emp4.full_name_nominative}")

        emp5, created = Employee.objects.get_or_create(
            full_name_nominative='Федоров Владимир Игоревич',
            defaults={
                'organization': org,
                'subdivision': pc2,
                'department': um2,
                'position': pos_worker2,
                'hire_date': timezone.now().date() - timedelta(days=365),
                'date_of_birth': timezone.now().date() - timedelta(days=365*30),
            }
        )
        self.stdout.write(f"  {'Создан' if created else 'Существует'}: {emp5.full_name_nominative}")

        # 6. Оборудование
        self.stdout.write("\nШаг 6: Создание оборудования")

        eq1, created = Equipment.objects.get_or_create(
            inventory_number='10000001',
            defaults={
                'equipment_name': 'Конвейер сборочный №1',
                'organization': org,
                'subdivision': pc1,
                'department': us1,
                'maintenance_period_months': 12,
                'last_maintenance_date': timezone.now().date() - timedelta(days=180),
            }
        )
        self.stdout.write(f"  {'Создано' if created else 'Существует'}: {eq1.equipment_name}")

        eq2, created = Equipment.objects.get_or_create(
            inventory_number='10000002',
            defaults={
                'equipment_name': 'Конвейер сборочный №2',
                'organization': org,
                'subdivision': pc1,
                'department': us1,
                'maintenance_period_months': 12,
                'last_maintenance_date': timezone.now().date() - timedelta(days=180),
            }
        )
        self.stdout.write(f"  {'Создано' if created else 'Существует'}: {eq2.equipment_name}")

        eq3, created = Equipment.objects.get_or_create(
            inventory_number='20000001',
            defaults={
                'equipment_name': 'Токарный станок 1К62',
                'organization': org,
                'subdivision': pc2,
                'department': um2,
                'maintenance_period_months': 12,
                'last_maintenance_date': timezone.now().date() - timedelta(days=180),
            }
        )
        self.stdout.write(f"  {'Создано' if created else 'Существует'}: {eq3.equipment_name}")

        # 7. СИЗ
        self.stdout.write("\nШаг 7: Создание СИЗ")

        siz1, created = SIZ.objects.get_or_create(
            name='Каска защитная',
            defaults={
                'classification': 'Средства защиты головы',
                'unit': 'шт',
                'wear_period': 36,
            }
        )
        self.stdout.write(f"  {'Создано' if created else 'Существует'}: {siz1.name}")

        siz2, created = SIZ.objects.get_or_create(
            name='Перчатки х/б',
            defaults={
                'classification': 'Средства защиты рук',
                'unit': 'пара',
                'wear_period': 1,
            }
        )
        self.stdout.write(f"  {'Создано' if created else 'Существует'}: {siz2.name}")

        # 8. Пользователи с правами
        self.stdout.write("\nШаг 8: Создание пользователей с правами")

        # Директор - доступ ко всей организации
        user1, created = User.objects.get_or_create(
            username='director',
            defaults={
                'email': 'director@testzavod.by',
                'first_name': 'Петр',
                'last_name': 'Петров',
                'is_staff': True,
            }
        )
        if created:
            user1.set_password('test123')
            user1.save()

        profile1, _ = Profile.objects.get_or_create(user=user1)
        profile1.organizations.set([org])
        self.stdout.write(f"  {'Создан' if created else 'Существует'}: director | Доступ: вся организация")

        # Начальник цеха - доступ к подразделению
        user2, created = User.objects.get_or_create(
            username='workshop_manager',
            defaults={
                'email': 'workshop@testzavod.by',
                'first_name': 'Сидор',
                'last_name': 'Сидоров',
                'is_staff': True,
            }
        )
        if created:
            user2.set_password('test123')
            user2.save()

        profile2, _ = Profile.objects.get_or_create(user=user2)
        profile2.subdivisions.set([pc1])
        self.stdout.write(f"  {'Создан' if created else 'Существует'}: workshop_manager | Доступ: Цех №1")

        # Мастер участка - доступ к отделу
        user3, created = User.objects.get_or_create(
            username='section_supervisor',
            defaults={
                'email': 'supervisor@testzavod.by',
                'first_name': 'Алексей',
                'last_name': 'Кузнецов',
                'is_staff': True,
            }
        )
        if created:
            user3.set_password('test123')
            user3.save()

        profile3, _ = Profile.objects.get_or_create(user=user3)
        profile3.departments.set([us1])
        self.stdout.write(f"  {'Создан' if created else 'Существует'}: section_supervisor | Доступ: Участок сборки")

        # Итоги
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS("ЗАВЕРШЕНО"))
        self.stdout.write("=" * 80)

        stats = f"""
Создано:
  - Организаций: 1
  - Подразделений: {StructuralSubdivision.objects.filter(organization=org).count()}
  - Отделов: {Department.objects.filter(organization=org).count()}
  - Должностей: {Position.objects.filter(organization=org).count()}
  - Сотрудников: {Employee.objects.filter(organization=org).count()}
  - Оборудования: {Equipment.objects.filter(organization=org).count()}
  - СИЗ: {SIZ.objects.count()}

Тестовые пользователи (пароль для всех: test123):
  1. director - Полный доступ к организации
  2. workshop_manager - Доступ к Цеху №1
  3. section_supervisor - Доступ к Участку сборки

Для тестирования войдите под каждым пользователем на:
  http://localhost:8001/directory/
"""
        self.stdout.write(stats)
