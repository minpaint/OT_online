from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from directory.models import Profile


class Command(BaseCommand):
    help = 'Создаёт Profile для пользователей, у которых его нет'

    def handle(self, *args, **options):
        users_without_profile = []

        for user in User.objects.all():
            if not hasattr(user, 'profile'):
                Profile.objects.create(user=user)
                users_without_profile.append(user.username)

        if users_without_profile:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Создано профилей: {len(users_without_profile)}'
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'Пользователи: {", ".join(users_without_profile)}'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('У всех пользователей уже есть профили')
            )
