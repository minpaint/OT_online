# directory/views/api.py
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
import logging

from directory.models import Position, MedicalExaminationNorm

# Настройка логирования
logger = logging.getLogger(__name__)


@login_required
@require_GET
def position_needs_step_info(request, position_id):
    """
    API для получения информации о том, нужны ли дополнительные шаги
    для выбранной должности
    """
    try:
        position = get_object_or_404(Position, pk=position_id)

        logger.debug(f"Запрос информации о шагах для должности ID={position_id} ({position.position_name})")

        # Проверяем медосмотр
        has_custom_medical = position.medical_factors.filter(is_disabled=False).exists()
        has_reference_medical = False

        if not has_custom_medical:
            has_reference_medical = MedicalExaminationNorm.objects.filter(
                position_name=position.position_name
            ).exists()

        needs_medical = has_custom_medical or has_reference_medical

        # Проверяем СИЗ
        has_custom_siz = position.siz_norms.exists()
        has_reference_siz = False

        if not has_custom_siz:
            has_reference_siz = Position.find_reference_norms(position.position_name).exists()

        needs_siz = has_custom_siz or has_reference_siz

        logger.debug(f"Результат для должности {position.position_name}: "
                     f"needs_medical={needs_medical}, needs_siz={needs_siz}")

        return JsonResponse({
            'position_id': position.id,
            'position_name': position.position_name,
            'needs_medical': needs_medical,
            'needs_siz': needs_siz
        })

    except Exception as e:
        logger.error(f"Ошибка при получении информации о должности ID={position_id}: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': 'Ошибка при получении информации о должности',
            'message': str(e)
        }, status=500)