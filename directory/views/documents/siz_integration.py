# Добавьте эту функцию в directory/views/documents/siz_integration.py

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

    employee = get_object_or_404(Employee, pk=employee_id)

    # Получаем выбранные нормы СИЗ из GET-параметров
    selected_norm_ids = request.GET.getlist('selected_norms', [])

    # Создаем контекст с выбранными нормами
    custom_context = {'selected_norm_ids': selected_norm_ids} if selected_norm_ids else None

    # Генерируем документ
    document = generate_siz_card_docx(employee, request.user, custom_context)

    if document:
        # Возвращаем файл для скачивания
        response = HttpResponse(
            document.document_file.read(),
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        response['Content-Disposition'] = f'attachment; filename="SIZ_Card_{employee.id}.docx"'
        return response
    else:
        # Обработка ошибки
        messages.error(request, "Не удалось сгенерировать карточку СИЗ")
        return redirect('directory:siz:siz_personal_card', employee_id=employee_id)