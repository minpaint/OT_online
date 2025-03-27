"""
📂 Команда для инициализации шаблонов документов

Эта команда создает начальные записи шаблонов документов в базе данных,
что позволяет использовать функциональность генерации документов
сразу после установки приложения.
"""
import os
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.core.files.base import ContentFile

from directory.models.document_template import DocumentTemplate


class Command(BaseCommand):
    help = 'Инициализирует шаблоны документов для генерации'

    def handle(self, *args, **options):
        # Определяем базовую директорию для шаблонов
        templates_dir = os.path.join(settings.BASE_DIR, 'directory', 'data', 'templates')

        # Проверяем существование директории
        if not os.path.exists(templates_dir):
            os.makedirs(templates_dir)

        # Создаем шаблоны, если они отсутствуют
        self._create_internship_order_template(templates_dir)
        self._create_admission_order_template(templates_dir)

        self.stdout.write(self.style.SUCCESS('Шаблоны документов успешно инициализированы'))

    def _create_internship_order_template(self, templates_dir):
        """
        Создает шаблон распоряжения о стажировке
        """
        # Проверяем, существует ли уже такой шаблон в базе
        if DocumentTemplate.objects.filter(document_type='internship_order').exists():
            self.stdout.write('Шаблон распоряжения о стажировке уже существует')
            return

        # Путь к файлу шаблона
        template_path = os.path.join(templates_dir, 'internship_order_template.docx')

        # Если файл шаблона отсутствует, создаем заглушку
        if not os.path.exists(template_path):
            self.stdout.write(self.style.WARNING(
                f'Файл шаблона {template_path} не найден, создается заглушка'
            ))

            # Создаем объект шаблона в базе
            template = DocumentTemplate(
                name='Распоряжение о стажировке',
                description='Шаблон распоряжения об установлении стажировки сотруднику',
                document_type='internship_order',
                is_active=True
            )

            # Создаем простой placeholder-файл
            placeholder_content = (
                "Шаблон документа: Распоряжение о стажировке\n\n"
                "Это временный placeholder-файл. Пожалуйста, замените его "
                "на реальный шаблон DOCX согласно инструкции в документации."
            )

            # Создаем временный файл
            file_content = ContentFile(placeholder_content.encode('utf-8'))
            template.template_file.save('internship_order_template.docx', file_content)

            self.stdout.write(self.style.SUCCESS('Создан шаблон распоряжения о стажировке'))
        else:
            # Загружаем существующий файл шаблона
            with open(template_path, 'rb') as f:
                file_content = ContentFile(f.read())

            # Создаем объект шаблона в базе
            template = DocumentTemplate(
                name='Распоряжение о стажировке',
                description='Шаблон распоряжения об установлении стажировки сотруднику',
                document_type='internship_order',
                is_active=True
            )
            template.template_file.save('internship_order_template.docx', file_content)

            self.stdout.write(self.style.SUCCESS(
                f'Создан шаблон распоряжения о стажировке из файла {template_path}'
            ))

    def _create_admission_order_template(self, templates_dir):
        """
        Создает шаблон распоряжения о допуске к самостоятельной работе
        """
        # Проверяем, существует ли уже такой шаблон в базе
        if DocumentTemplate.objects.filter(document_type='admission_order').exists():
            self.stdout.write('Шаблон распоряжения о допуске к самостоятельной работе уже существует')
            return

        # Путь к файлу шаблона
        template_path = os.path.join(templates_dir, 'admission_order_template.docx')

        # Если файл шаблона отсутствует, создаем заглушку
        if not os.path.exists(template_path):
            self.stdout.write(self.style.WARNING(
                f'Файл шаблона {template_path} не найден, создается заглушка'
            ))

            # Создаем объект шаблона в базе
            template = DocumentTemplate(
                name='Распоряжение о допуске к самостоятельной работе',
                description='Шаблон распоряжения о допуске сотрудника к самостоятельной работе',
                document_type='admission_order',
                is_active=True
            )

            # Создаем простой placeholder-файл
            placeholder_content = (
                "Шаблон документа: Распоряжение о допуске к самостоятельной работе\n\n"
                "Это временный placeholder-файл. Пожалуйста, замените его "
                "на реальный шаблон DOCX согласно инструкции в документации."
            )

            # Создаем временный файл
            file_content = ContentFile(placeholder_content.encode('utf-8'))
            template.template_file.save('admission_order_template.docx', file_content)

            self.stdout.write(self.style.SUCCESS(
                'Создан шаблон распоряжения о допуске к самостоятельной работе'
            ))
        else:
            # Загружаем существующий файл шаблона
            with open(template_path, 'rb') as f:
                file_content = ContentFile(f.read())

            # Создаем объект шаблона в базе
            template = DocumentTemplate(
                name='Распоряжение о допуске к самостоятельной работе',
                description='Шаблон распоряжения о допуске сотрудника к самостоятельной работе',
                document_type='admission_order',
                is_active=True
            )
            template.template_file.save('admission_order_template.docx', file_content)

            self.stdout.write(self.style.SUCCESS(
                f'Создан шаблон распоряжения о допуске к самостоятельной работе из файла {template_path}'
            ))