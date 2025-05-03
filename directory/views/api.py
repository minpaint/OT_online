# directory/views/api.py
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from directory.models import Position, MedicalExaminationNorm


@login_required
def position_needs_step_info(request, position_id):
    """
    API для получения информации о том, нужны ли дополнительные шаги
    для выбранной должности
    """
    position = get_object_or_404(Position, pk=position_id)

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

    return JsonResponse({
        'position_id': position.id,
        'position_name': position.position_name,
        'needs_medical': needs_medical,
        'needs_siz': needs_siz
    })