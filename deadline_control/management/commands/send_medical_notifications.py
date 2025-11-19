# deadline_control/management/commands/send_medical_notifications.py
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model

from directory.models import Employee, Organization
from deadline_control.models import EmailSettings
from datetime import datetime

User = get_user_model()


class Command(BaseCommand):
    help = 'Отправляет email уведомления о плане прохождения медицинских осмотров (2 раза в месяц)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--emails',
            type=str,
            help='Список email адресов через запятую (по умолчанию - администраторы)',
        )
        parser.add_argument(
            '--organization',
            type=int,
            help='ID организации для фильтрации (по умолчанию - все)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Начинаем формирование отчета о медосмотрах...'))

        # Определяем организации для обработки
        if options['organization']:
            organizations = Organization.objects.filter(id=options['organization'])
        else:
            organizations = Organization.objects.all()

        total_sent = 0
        total_failed = 0

        # Обрабатываем каждую организацию отдельно
        for organization in organizations:
            self.stdout.write(f'\n--- Обработка организации: {organization.short_name_ru} ---')

            # Получаем настройки email для организации
            try:
                email_settings = EmailSettings.get_settings(organization)
            except Exception as e:
                self.stdout.write(self.style.WARNING(
                    f'Не удалось получить настройки email для {organization.short_name_ru}: {e}'
                ))
                continue

            # Проверяем, активны ли настройки
            if not email_settings.is_active:
                self.stdout.write(self.style.WARNING(
                    f'Email уведомления отключены для {organization.short_name_ru}'
                ))
                continue

            if not email_settings.email_host:
                self.stdout.write(self.style.WARNING(
                    f'SMTP сервер не настроен для {organization.short_name_ru}'
                ))
                continue

            # Определяем получателей
            if options['emails']:
                recipient_list = [email.strip() for email in options['emails'].split(',')]
            else:
                # Используем получателей из настроек организации
                recipient_list = email_settings.get_recipient_list()

                # Если в настройках не указаны получатели - берём администраторов
                if not recipient_list:
                    recipient_list = list(
                        User.objects.filter(is_staff=True, email__isnull=False)
                        .exclude(email='')
                        .values_list('email', flat=True)
                    )

            if not recipient_list:
                self.stdout.write(self.style.WARNING(
                    f'Нет получателей для {organization.short_name_ru}'
                ))
                continue

            # Получаем сотрудников организации с медосмотрами
            employees_qs = Employee.objects.filter(
                organization=organization,
                medical_examinations__isnull=False
            ).distinct()

            employees_qs = employees_qs.select_related(
                'organization',
                'position'
            ).prefetch_related(
                'medical_examinations__harmful_factor'
            )

            # Разделяем на категории
            no_date = []
            overdue = []
            upcoming = []

            for employee in employees_qs:
                medical_status = employee.get_medical_status()

                if not medical_status:
                    continue

                status = medical_status['status']
                if status == 'no_date':
                    no_date.append({
                        'employee': employee,
                        'status': medical_status
                    })
                elif status == 'expired':
                    overdue.append({
                        'employee': employee,
                        'status': medical_status
                    })
                elif status == 'upcoming':
                    upcoming.append({
                        'employee': employee,
                        'status': medical_status
                    })

            # Если нет данных для отправки - пропускаем
            if not (no_date or overdue or upcoming):
                self.stdout.write(self.style.WARNING(
                    f'Нет данных для отправки для {organization.short_name_ru}'
                ))
                continue

            # Формируем текст письма
            subject = f'📋 План прохождения медицинских осмотров - {organization.short_name_ru} - {datetime.now().strftime("%d.%m.%Y")}'
            message = self._format_email_message(organization, no_date, overdue, upcoming)

            # Получаем подключение с настройками организации
            connection = email_settings.get_connection()
            from_email = email_settings.default_from_email or email_settings.email_host_user

            # Отправляем письмо
            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=from_email,
                    recipient_list=recipient_list,
                    connection=connection,
                    fail_silently=False,
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Уведомление отправлено для {organization.short_name_ru}!\n'
                        f'   Получатели: {", ".join(recipient_list)}\n'
                        f'   Без даты: {len(no_date)}, Просроченные: {len(overdue)}, Предстоящие: {len(upcoming)}'
                    )
                )
                total_sent += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Ошибка при отправке email для {organization.short_name_ru}: {str(e)}')
                )
                total_failed += 1

        # Итоговая статистика
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(
            self.style.SUCCESS(f'Завершено! Отправлено: {total_sent}, Ошибок: {total_failed}')
        )

    def _format_email_message(self, organization, no_date, overdue, upcoming):
        """Форматирует текст email сообщения"""
        lines = []
        lines.append('📋 ПЛАН ПРОХОЖДЕНИЯ МЕДИЦИНСКИХ ОСМОТРОВ')
        lines.append('=' * 60)
        lines.append(f'Организация: {organization.full_name_ru}')
        lines.append(f'Дата отчета: {datetime.now().strftime("%d.%m.%Y %H:%M")}')
        lines.append('')

        # Без даты
        if no_date:
            lines.append(f'📋 ТРЕБУЕТСЯ ВНЕСТИ ДАТУ МЕДОСМОТРА ({len(no_date)} сотрудников):')
            lines.append('-' * 60)
            for item in no_date:
                emp = item['employee']
                status = item['status']
                factors = ', '.join([f['short_name'] for f in status['factors']])
                lines.append(
                    f'  • {emp.full_name_nominative}\n'
                    f'    Должность: {emp.position.position_name}\n'
                    f'    Организация: {emp.organization.short_name_ru}\n'
                    f'    Факторы: {factors}\n'
                    f'    Мин. периодичность: {status["min_periodicity"]} мес.\n'
                )
            lines.append('')

        # Просроченные
        if overdue:
            lines.append(f'🚨 ПРОСРОЧЕННЫЕ МЕДОСМОТРЫ ({len(overdue)} сотрудников):')
            lines.append('-' * 60)
            for item in overdue:
                emp = item['employee']
                status = item['status']
                factors = ', '.join([f['short_name'] for f in status['factors']])
                days_overdue = abs(status['days_until'])
                lines.append(
                    f'  • {emp.full_name_nominative}\n'
                    f'    Должность: {emp.position.position_name}\n'
                    f'    Организация: {emp.organization.short_name_ru}\n'
                    f'    Факторы: {factors}\n'
                    f'    Дата МО: {status["date_completed"].strftime("%d.%m.%Y")}\n'
                    f'    Просрочено: {days_overdue} дней\n'
                )
            lines.append('')

        # Предстоящие
        if upcoming:
            lines.append(f'⚠️ ПРЕДСТОЯЩИЕ МЕДОСМОТРЫ ({len(upcoming)} сотрудников):')
            lines.append('-' * 60)
            for item in upcoming:
                emp = item['employee']
                status = item['status']
                factors = ', '.join([f['short_name'] for f in status['factors']])
                lines.append(
                    f'  • {emp.full_name_nominative}\n'
                    f'    Должность: {emp.position.position_name}\n'
                    f'    Организация: {emp.organization.short_name_ru}\n'
                    f'    Факторы: {factors}\n'
                    f'    Следующий МО: {status["next_date"].strftime("%d.%m.%Y")}\n'
                    f'    Осталось: {status["days_until"]} дней\n'
                )
            lines.append('')

        # Итого
        lines.append('=' * 60)
        lines.append(f'ИТОГО: Без даты: {len(no_date)}, Просроченные: {len(overdue)}, Предстоящие: {len(upcoming)}')
        lines.append('')
        lines.append('---')
        lines.append('Это автоматическое уведомление из системы управления охраной труда OT_online')

        return '\n'.join(lines)
