"""
Management команда для создания профилей пользователей и настройки доступа к организациям.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from directory.models import Profile, Organization


class Command(BaseCommand):
    help = 'Создает профили для всех пользователей и настраивает доступ к организациям'

    def add_arguments(self, parser):
        parser.add_argument(
            '--grant-staff-access',
            action='store_true',
            help='Автоматически предоставить staff пользователям доступ ко всем организациям'
        )

    def handle(self, *args, **options):
        users_without_profile = []
        users_without_orgs = []

        # Создаем профили для всех пользователей
        for user in User.objects.all():
            profile, created = Profile.objects.get_or_create(user=user)
            if created:
                users_without_profile.append(user.username)
                self.stdout.write(
                    self.style.SUCCESS(f'[OK] Создан профиль для пользователя: {user.username}')
                )

            # Настройка доступа для staff пользователей
            if options['grant_staff_access'] and user.is_staff and not user.is_superuser:
                if profile.organizations.count() == 0:
                    orgs = Organization.objects.all()
                    profile.organizations.set(orgs)
                    users_without_orgs.append(user.username)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'[OK] Предоставлен доступ ко всем организациям для: {user.username}'
                        )
                    )

        # Итоговая статистика
        if users_without_profile:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n[STATS] Создано профилей: {len(users_without_profile)}'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('\n[OK] Все пользователи уже имеют профили')
            )

        if options['grant_staff_access']:
            if users_without_orgs:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'[STATS] Настроен доступ для staff пользователей: {len(users_without_orgs)}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('[OK] Все staff пользователи уже имеют доступ к организациям')
                )
