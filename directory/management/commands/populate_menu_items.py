# directory/management/commands/populate_menu_items.py
"""
Management команда для заполнения начальных пунктов меню в базе данных.

Создает структуру меню на основе текущей разметки base.html:
- Боковое меню (sidebar)
- Верхнее меню (top)

Usage:
    py manage.py populate_menu_items
    py manage.py populate_menu_items --clear  # Очистить перед заполнением
"""

from django.core.management.base import BaseCommand
from directory.models import MenuItem


class Command(BaseCommand):
    help = 'Заполняет базу данных начальными пунктами меню системы'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Удалить все существующие пункты меню перед заполнением',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Очистка существующих пунктов меню...'))
            MenuItem.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('OK: Все пункты меню удалены'))

        # Счетчики
        created_count = 0
        skipped_count = 0

        # ========================================
        # БОКОВОЕ МЕНЮ (SIDEBAR)
        # ========================================

        # 1. Основное (раздел-заголовок)
        separator_main, created = MenuItem.objects.get_or_create(
            name='Основное',
            location='sidebar',
            defaults={
                'is_separator': True,
                'order': 10,
                'is_active': True,
                'requires_auth': True,
            }
        )
        if created:
            created_count += 1
            self.stdout.write(f'  OK: Создан раздел: {separator_main.name}')
        else:
            skipped_count += 1

        # 1.1 Вводный инструктаж (первый пункт)
        briefing_item, created = MenuItem.objects.get_or_create(
            name='Вводный инструктаж',
            url_name='directory:introductory_briefing',
            location='sidebar',
            defaults={
                'icon': '📺',
                'order': 11,
                'is_active': True,
                'requires_auth': True,
            }
        )
        if created:
            created_count += 1
            self.stdout.write(f'  OK: Создан пункт: {briefing_item.name}')
        else:
            skipped_count += 1

        # 1.2 Сотрудники (главная страница)
        employees_item, created = MenuItem.objects.get_or_create(
            name='Сотрудники',
            url_name='directory:home',
            location='sidebar',
            defaults={
                'icon': '👥',
                'order': 12,
                'is_active': True,
                'requires_auth': True,
            }
        )
        if created:
            created_count += 1
            self.stdout.write(f'  OK: Создан пункт: {employees_item.name}')
        else:
            skipped_count += 1

        # 1.3 Приемы на работу
        hiring_item, created = MenuItem.objects.get_or_create(
            name='Приемы на работу',
            url_name='directory:hiring:hiring_list',
            location='sidebar',
            defaults={
                'icon': '➕',
                'order': 13,
                'is_active': True,
                'requires_auth': True,
            }
        )
        if created:
            created_count += 1
            self.stdout.write(f'  OK: Создан пункт: {hiring_item.name}')
        else:
            skipped_count += 1

        # 2. Контроль сроков (раздел-заголовок)
        separator_deadlines, created = MenuItem.objects.get_or_create(
            name='Контроль сроков',
            location='sidebar',
            defaults={
                'icon': '⏰',
                'is_separator': True,
                'order': 20,
                'is_active': True,
                'requires_auth': True,
            }
        )
        if created:
            created_count += 1
            self.stdout.write(f'  OK: Создан раздел: {separator_deadlines.name}')
        else:
            skipped_count += 1

        # 2.1 Dashboard
        dashboard_item, created = MenuItem.objects.get_or_create(
            name='Dashboard',
            url_name='deadline_control:dashboard',
            location='sidebar',
            defaults={
                'icon': '📊',
                'order': 21,
                'is_active': True,
                'requires_auth': True,
            }
        )
        if created:
            created_count += 1
            self.stdout.write(f'  OK: Создан пункт: {dashboard_item.name}')
        else:
            skipped_count += 1

        # 2.2 ТО оборудования
        equipment_item, created = MenuItem.objects.get_or_create(
            name='ТО оборудования',
            url_name='deadline_control:equipment:list',
            location='sidebar',
            defaults={
                'icon': '⚙️',
                'order': 22,
                'is_active': True,
                'requires_auth': True,
            }
        )
        if created:
            created_count += 1
            self.stdout.write(f'  OK: Создан пункт: {equipment_item.name}')
        else:
            skipped_count += 1

        # 2.3 Ключевые сроки
        deadlines_item, created = MenuItem.objects.get_or_create(
            name='Ключевые сроки',
            url_name='deadline_control:key_deadline:list',
            location='sidebar',
            defaults={
                'icon': '📅',
                'order': 23,
                'is_active': True,
                'requires_auth': True,
            }
        )
        if created:
            created_count += 1
            self.stdout.write(f'  OK: Создан пункт: {deadlines_item.name}')
        else:
            skipped_count += 1

        # 2.4 Медосмотры
        medical_item, created = MenuItem.objects.get_or_create(
            name='Медосмотры',
            url_name='deadline_control:medical:list',
            location='sidebar',
            defaults={
                'icon': '🏥',
                'order': 24,
                'is_active': True,
                'requires_auth': True,
            }
        )
        if created:
            created_count += 1
            self.stdout.write(f'  OK: Создан пункт: {medical_item.name}')
        else:
            skipped_count += 1

        # 3. Дополнительно (раздел-заголовок)
        separator_additional, created = MenuItem.objects.get_or_create(
            name='Дополнительно',
            location='sidebar',
            defaults={
                'is_separator': True,
                'order': 30,
                'is_active': True,
                'requires_auth': True,
            }
        )
        if created:
            created_count += 1
            self.stdout.write(f'  OK: Создан раздел: {separator_additional.name}')
        else:
            skipped_count += 1

        # 3.1 Экзамены
        quiz_item, created = MenuItem.objects.get_or_create(
            name='Экзамены',
            url_name='directory:quiz:quiz_list',
            location='sidebar',
            defaults={
                'icon': '📝',
                'order': 31,
                'is_active': True,
                'requires_auth': True,
            }
        )
        if created:
            created_count += 1
            self.stdout.write(f'  OK: Создан пункт: {quiz_item.name}')
        else:
            skipped_count += 1

        # 3.2 Комиссии
        commissions_item, created = MenuItem.objects.get_or_create(
            name='Комиссии',
            url_name='directory:commissions:commission_list',
            location='sidebar',
            defaults={
                'icon': '👥',
                'order': 32,
                'is_active': True,
                'requires_auth': True,
            }
        )
        if created:
            created_count += 1
            self.stdout.write(f'  OK: Создан пункт: {commissions_item.name}')
        else:
            skipped_count += 1

        # ========================================
        # ВЕРХНЕЕ МЕНЮ (TOP BAR)
        # ========================================

        # 4.1 Принять на работу
        hiring_action_item, created = MenuItem.objects.get_or_create(
            name='Принять на работу',
            url_name='directory:hiring:simple_hiring',
            location='top',
            defaults={
                'icon': '➕',
                'order': 41,
                'is_active': True,
                'requires_auth': True,
                'description': 'Кнопка быстрого доступа к форме приема на работу',
            }
        )
        if created:
            created_count += 1
            self.stdout.write(f'  OK: Создан пункт (верхнее меню): {hiring_action_item.name}')
        else:
            skipped_count += 1

        # 4.2 Выдать направление кандидату
        referral_item, created = MenuItem.objects.get_or_create(
            name='Выдать направление кандидату',
            url_name='deadline_control:medical:referral_new_employee',
            location='top',
            defaults={
                'icon': '🏥',
                'order': 42,
                'is_active': True,
                'requires_auth': True,
                'description': 'Кнопка быстрого доступа к форме выдачи направления на медосмотр',
            }
        )
        if created:
            created_count += 1
            self.stdout.write(f'  OK: Создан пункт (верхнее меню): {referral_item.name}')
        else:
            skipped_count += 1

        # 4.3 Администрирование (для staff)
        admin_item, created = MenuItem.objects.get_or_create(
            name='Администрирование',
            url_name='admin:index',
            location='top',
            defaults={
                'icon': '⚙️',
                'order': 43,
                'is_active': True,
                'requires_auth': True,
                'description': 'Доступ к административной панели Django (только для staff)',
            }
        )
        if created:
            created_count += 1
            self.stdout.write(f'  OK: Создан пункт (верхнее меню): {admin_item.name}')
        else:
            skipped_count += 1

        # Итоги
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS(f'OK: Заполнение завершено!'))
        self.stdout.write(self.style.SUCCESS(f'  Создано: {created_count}'))
        self.stdout.write(self.style.SUCCESS(f'  Пропущено (уже существует): {skipped_count}'))
        self.stdout.write(self.style.SUCCESS(f'  Всего пунктов меню: {MenuItem.objects.count()}'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
