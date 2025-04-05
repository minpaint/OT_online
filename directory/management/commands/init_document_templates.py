# D:\YandexDisk\OT_online\directory\management\commands\init_document_templates.py
"""
📂 Команда для инициализации шаблонов документов

Эта команда создает начальные записи шаблонов документов в базе данных,
что позволяет использовать функциональность генерации документов
сразу после установки приложения.
"""
import os
import logging
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.core.files.base import ContentFile

from directory.models.document_template import DocumentTemplate

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Инициализирует шаблоны документов для генерации'

    def handle(self, *args, **options):
        # Определяем базовую директорию для шаблонов
        templates_dir = os.path.join(settings.BASE_DIR, 'directory', 'data', 'templates')

        # Проверяем существование директории
        if not os.path.exists(templates_dir):
            os.makedirs(templates_dir)
            self.stdout.write(self.style.WARNING(f'Создана директория {templates_dir}'))

        # Создаем шаблоны, если они отсутствуют
        self._create_all_orders_template(templates_dir)
        self._create_knowledge_protocol_template(templates_dir)
        self._create_doc_familiarization_template(templates_dir)
        self._create_siz_card_template(templates_dir)

        self.stdout.write(self.style.SUCCESS('Шаблоны документов успешно инициализированы'))

    def _create_all_orders_template(self, templates_dir):
        """
        Создает шаблон распоряжений о стажировке
        """
        # Проверяем, существует ли уже такой шаблон в базе
        if DocumentTemplate.objects.filter(document_type='all_orders').exists():
            self.stdout.write('Шаблон распоряжений о стажировке уже существует')
            return

        # Путь к файлу шаблона
        template_path = os.path.join(templates_dir, 'all_order_template.docx')

        # Если файл шаблона отсутствует, создаем заглушку
        if not os.path.exists(template_path):
            self.stdout.write(self.style.WARNING(
                f'Файл шаблона {template_path} не найден, создается заглушка'
            ))

            # Создаем объект шаблона в базе
            template = DocumentTemplate(
                name='Распоряжения о стажировке',
                description='Шаблон для генерации распоряжений о стажировке и допуске к работе',
                document_type='all_orders',
                is_active=True
            )

            # Создаем простой placeholder-файл
            placeholder_content = (
                "Шаблон документа: Распоряжения о стажировке\n\n"
                "Это временный placeholder-файл. Пожалуйста, замените его "
                "на реальный шаблон DOCX согласно инструкции в документации."
            )

            # Создаем временный файл
            file_content = ContentFile(placeholder_content.encode('utf-8'))
            template.template_file.save('all_order_template.docx', file_content)

            self.stdout.write(self.style.SUCCESS('Создан шаблон распоряжений о стажировке'))
        else:
            # Загружаем существующий файл шаблона
            with open(template_path, 'rb') as f:
                file_content = ContentFile(f.read())

            # Создаем объект шаблона в базе
            template = DocumentTemplate(
                name='Распоряжения о стажировке',
                description='Шаблон для генерации распоряжений о стажировке и допуске к работе',
                document_type='all_orders',
                is_active=True
            )
            template.template_file.save('all_order_template.docx', file_content)

            self.stdout.write(self.style.SUCCESS(
                f'Создан шаблон распоряжений о стажировке из файла {template_path}'
            ))

    def _create_knowledge_protocol_template(self, templates_dir):
        """
        Создает шаблон протокола проверки знаний по охране труда
        """
        # Проверяем, существует ли уже такой шаблон в базе
        if DocumentTemplate.objects.filter(document_type='knowledge_protocol').exists():
            self.stdout.write('Шаблон протокола проверки знаний уже существует')
            return

        # Путь к файлу шаблона
        template_path = os.path.join(templates_dir, 'knowledge_protocol_template.docx')

        # Если файл шаблона отсутствует, создаем заглушку
        if not os.path.exists(template_path):
            self.stdout.write(self.style.WARNING(
                f'Файл шаблона {template_path} не найден, создается заглушка'
            ))

            # Создаем объект шаблона в базе
            template = DocumentTemplate(
                name='Протокол проверки знаний',
                description='Шаблон протокола проверки знаний по охране труда',
                document_type='knowledge_protocol',
                is_active=True
            )

            # Создаем простой placeholder-файл
            placeholder_content = (
                "Шаблон документа: Протокол проверки знаний по охране труда\n\n"
                "Это временный placeholder-файл. Пожалуйста, замените его "
                "на реальный шаблон DOCX согласно инструкции в документации."
            )

            # Создаем временный файл
            file_content = ContentFile(placeholder_content.encode('utf-8'))
            template.template_file.save('knowledge_protocol_template.docx', file_content)

            self.stdout.write(self.style.SUCCESS(
                'Создан шаблон протокола проверки знаний'
            ))
        else:
            # Загружаем существующий файл шаблона
            with open(template_path, 'rb') as f:
                file_content = ContentFile(f.read())

            # Создаем объект шаблона в базе
            template = DocumentTemplate(
                name='Протокол проверки знаний',
                description='Шаблон протокола проверки знаний по охране труда',
                document_type='knowledge_protocol',
                is_active=True
            )
            template.template_file.save('knowledge_protocol_template.docx', file_content)

            self.stdout.write(self.style.SUCCESS(
                f'Создан шаблон протокола проверки знаний из файла {template_path}'
            ))

    def _create_doc_familiarization_template(self, templates_dir):
        """
        Создает шаблон листа ознакомления с документами
        """
        # Проверяем, существует ли уже такой шаблон в базе
        if DocumentTemplate.objects.filter(document_type='doc_familiarization').exists():
            self.stdout.write('Шаблон листа ознакомления с документами уже существует')
            return

        # Путь к файлу шаблона
        template_path = os.path.join(templates_dir, 'doc_familiarization_template.docx')

        # Если файл шаблона отсутствует, создаем заглушку
        if not os.path.exists(template_path):
            self.stdout.write(self.style.WARNING(
                f'Файл шаблона {template_path} не найден, создается заглушка'
            ))

            # Создаем объект шаблона в базе
            template = DocumentTemplate(
                name='Лист ознакомления с документами',
                description='Шаблон листа ознакомления сотрудника с документами',
                document_type='doc_familiarization',
                is_active=True
            )

            # Создаем простой placeholder-файл
            placeholder_content = (
                "Шаблон документа: Лист ознакомления с документами\n\n"
                "Это временный placeholder-файл. Пожалуйста, замените его "
                "на реальный шаблон DOCX согласно инструкции в документации."
            )

            # Создаем временный файл
            file_content = ContentFile(placeholder_content.encode('utf-8'))
            template.template_file.save('doc_familiarization_template.docx', file_content)

            self.stdout.write(self.style.SUCCESS(
                'Создан шаблон листа ознакомления с документами'
            ))
        else:
            # Загружаем существующий файл шаблона
            with open(template_path, 'rb') as f:
                file_content = ContentFile(f.read())

            # Создаем объект шаблона в базе
            template = DocumentTemplate(
                name='Лист ознакомления с документами',
                description='Шаблон листа ознакомления сотрудника с документами',
                document_type='doc_familiarization',
                is_active=True
            )
            template.template_file.save('doc_familiarization_template.docx', file_content)

            self.stdout.write(self.style.SUCCESS(
                f'Создан шаблон листа ознакомления с документами из файла {template_path}'
            ))

    def _create_siz_card_template(self, templates_dir):
        """
        Создает шаблон карточки учета СИЗ
        """
        # Проверяем, существует ли уже такой шаблон в базе
        if DocumentTemplate.objects.filter(document_type='siz_card').exists():
            self.stdout.write('Шаблон карточки учета СИЗ уже существует')
            return

        # Для карточки СИЗ используется существующий механизм генерации,
        # поэтому нам не нужен физический файл шаблона
        template = DocumentTemplate(
            name='Карточка учета СИЗ',
            description='Карточка учета выдачи средств индивидуальной защиты',
            document_type='siz_card',
            is_active=True
        )

        # Создаем фиктивный файл (он не будет использоваться)
        placeholder_content = (
            "Шаблон документа: Карточка учета СИЗ\n\n"
            "Этот файл не используется для генерации документа. "
            "Вместо него используется существующий механизм генерации карточки СИЗ в PDF."
        )

        file_content = ContentFile(placeholder_content.encode('utf-8'))
        template.template_file.save('siz_card_template.txt', file_content)

        self.stdout.write(self.style.SUCCESS(
            'Создан шаблон карточки учета СИЗ'
        ))