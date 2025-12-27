# Добавьте эту функцию в directory/views/documents/siz_integration.py
import logging

logger = logging.getLogger(__name__)

def generate_siz_card_docx_view(request, employee_id):
    """
    Представление для генерации карточки СИЗ в формате DOCX.

    Args:
        request: HttpRequest объект
        employee_id: ID сотрудника

    Returns:
        HttpResponse с файлом DOCX
    """
    from django.shortcuts import get_object_or_404, redirect
    from django.contrib import messages
    from django.http import HttpResponse
    from directory.models import Employee
    from directory.document_generators.siz_card_docx_generator import generate_siz_card_docx
    from directory.utils.permissions import AccessControlHelper
    from urllib.parse import quote

    employee = get_object_or_404(Employee, pk=employee_id)

    # Проверка прав доступа
    if not AccessControlHelper.can_access_object(request.user, employee):
        messages.error(request, "У вас нет доступа к этому сотруднику")
        return redirect('directory:employee_home')

    logger.info(f"Запрос на генерацию карточки СИЗ для сотрудника ID={employee_id}: {employee.full_name_nominative}")

    # Получаем выбранные нормы СИЗ из GET-параметров
    selected_norm_ids = request.GET.getlist('selected_norms', [])
    logger.info(f"Выбрано норм СИЗ: {len(selected_norm_ids)}, IDs: {selected_norm_ids}")

    # Создаем контекст с выбранными нормами
    custom_context = {'selected_norm_ids': selected_norm_ids} if selected_norm_ids else None

    # Генерируем документ
    result = generate_siz_card_docx(employee, request.user, custom_context)

    if result and 'content' in result and 'filename' in result:
        logger.info(f"Карточка СИЗ успешно сгенерирована, размер: {len(result['content'])} байт")
        # Возвращаем файл для скачивания
        response = HttpResponse(
            result['content'],
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        # Кодируем имя файла для поддержки кириллицы
        encoded_filename = quote(result['filename'])
        response['Content-Disposition'] = f"attachment; filename*=UTF-8''{encoded_filename}"
        return response
    else:
        # Обработка ошибки
        logger.error(f"Не удалось сгенерировать карточку СИЗ для сотрудника ID={employee_id}")
        messages.error(request, "Не удалось сгенерировать карточку СИЗ. Проверьте, что шаблон документа загружен и активен.")
        return redirect('directory:siz:siz_personal_card', employee_id=employee_id)