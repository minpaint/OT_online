from django.core.management.base import BaseCommand
from directory.utils.medical_examination import update_medical_examination_statuses


class Command(BaseCommand):
    help = 'Обновляет статусы медицинских осмотров'

    def handle(self, *args, **options):
        result = update_medical_examination_statuses()

        self.stdout.write(
            self.style.SUCCESS(
                f'Обновлено статусов: to_issue={result["to_issue_updated"]}, expired={result["expired_updated"]}'
            )
        )