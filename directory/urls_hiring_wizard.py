# -*- coding: utf-8 -*-
"""
🔗 URL-маршруты для многошаговой формы приема на работу
Добавьте это в основной urls.py
"""
from django.urls import path
from directory.views.hiring_wizard import HiringWizardView
from directory.views.api import position_needs_step_info

# URL-маршруты для многошаговой формы
urlpatterns = [
    # Многошаговая форма приема на работу
    path('hiring/wizard/', HiringWizardView.as_view(), name='hiring_wizard'),

    # API для проверки требуемых шагов
    path('api/position/<int:position_id>/needs_step_info/', 
         position_needs_step_info, 
         name='position_needs_step_info'),
]
