# D:\YandexDisk\OT_online\directory\views\documents\siz_integration.py
"""
🔄 Интеграция с существующим механизмом генерации карточки СИЗ

Этот модуль содержит функции для интеграции системы генерации документов
с существующим механизмом генерации карточки учета СИЗ.
"""
import os
import tempfile
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.utils.translation import gettext as _

from directory.models import Employee
from directory.models.document_template import DocumentTemplate, GeneratedDocument
from directory.utils.excel_export import generate_card_excel


def generate_siz_card_excel(request, employee_id):
    """
    Генерирует карточку учета СИЗ в формате Excel и сохраняет информацию о генерации.

    Args:
        request: Объект запроса
        employee_id: ID сотрудника

    Returns:
        HttpResponse с файлом Excel или перенаправление с сообщением об ошибке
    """
    try:
        # Получаем сотрудника
        employee = get_object_or_404(Employee, id=employee_id)

        # Генерируем Excel-файл с помощью существующего механизма
        response = generate_card_excel(request, employee_id)

        # Если функция вернула не FileResponse, значит, произошла ошибка
        if not isinstance(response, FileResponse):
            messages.error(request, _('Ошибка при генерации карточки учета СИЗ'))
            return redirect('directory:siz:siz_personal_card', employee_id=employee_id)

        # Создаем временный файл для сохранения информации о генерации
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            # Копируем содержимое из response в временный файл
            for chunk in response.streaming_content:
                tmp_file.write(chunk)

            # Получаем или создаем шаблон документа
            template, created = DocumentTemplate.objects.get_or_create(
                document_type='siz_card',
                defaults={
                    'name': 'Карточка учета СИЗ',
                    'description': 'Шаблон карточки учета выдачи средств индивидуальной защиты',
                    'is_active': True
                }
            )

            # Создаем запись о сгенерированном документе
            document = GeneratedDocument()
            document.template = template
            document.employee = employee
            document.created_by = request.user if request.user.is_authenticated else None

            # Формируем контекст с данными о генерации
            document_data = {
                'generated_at': str(document.created_at),
                'generated_by': str(document.created_by) if document.created_by else 'Система',
                'document_type': 'siz_card',
                'format': 'Excel'
            }
            document.document_data = document_data

            # Сохраняем файл в запись
            document.document_file.save(
                f'siz_card_{employee.full_name_nominative}_{document.created_at.strftime("%Y%m%d_%H%M%S")}.xlsx',
                open(tmp_file.name, 'rb')
            )
            document.save()

            # Удаляем временный файл
            try:
                os.unlink(tmp_file.name)
            except:
                pass

            messages.success(request, _('Карточка учета СИЗ успешно сгенерирована'))

            # Перенаправляем на страницу с документом
            return redirect('directory:documents:document_detail', pk=document.id)

    except Exception as e:
        messages.error(request, _(f'Ошибка при генерации карточки учета СИЗ: {str(e)}'))
        return redirect('directory:siz:siz_personal_card', employee_id=employee_id)