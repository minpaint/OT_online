# D:\YandexDisk\OT_online\directory\utils\docx_generator.py (часть файла)

def generate_all_orders(employee, user=None, custom_context=None):
    """
    Генерирует комбинированные распоряжения о стажировке и допуске для сотрудника.
    Args:
        employee: Объект модели Employee
        user: Пользователь, создающий документ (опционально)
        custom_context: Пользовательский контекст (опционально)
    Returns:
        Optional[GeneratedDocument]: Объект сгенерированного документа или None при ошибке
    """
    # Получаем шаблон для распоряжений о стажировке
    try:
        template = DocumentTemplate.objects.get(document_type='all_orders', is_active=True)
    except DocumentTemplate.DoesNotExist:
        raise ValueError("Активный шаблон для распоряжений о стажировке не найден")

    # Подготавливаем базовый контекст
    context = prepare_employee_context(employee)

    # Ищем руководителя стажировки с иерархическим подходом
    from directory.views.documents.utils import get_internship_leader

    internship_leader, level, success = get_internship_leader(employee)
    if success and internship_leader:
        context.update({
            'head_of_internship_name': internship_leader.full_name_nominative,
            'head_of_internship_name_initials': get_initials_from_name(internship_leader.full_name_nominative),
            'head_of_internship_position': internship_leader.position.position_name if internship_leader.position else "",
            'internship_leader_level': level,  # Добавляем для отладки
        })
    else:
        # Отмечаем как недостающие данные
        context['missing_data'].append("Руководитель стажировки")

    # Если есть пользовательский контекст, обновляем основной контекст
    if custom_context:
        # Проверяем наличие ключа missing_data в пользовательском контексте
        if 'missing_data' in custom_context:
            custom_missing_data = custom_context.pop('missing_data')
            # Объединяем списки недостающих данных
            context['missing_data'].extend(custom_missing_data)
            # Обновляем флаг наличия недостающих данных
            context['has_missing_data'] = len(context['missing_data']) > 0

        context.update(custom_context)

    # Генерируем документ
    return generate_docx_from_template(template.id, context, employee, user)