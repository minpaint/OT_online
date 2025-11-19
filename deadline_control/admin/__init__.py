"""
Админ-панель для приложения 'Контроль сроков'
"""
from .equipment import EquipmentAdmin
from .key_deadline import KeyDeadlineCategoryAdmin
from .medical_examination import (
    MedicalExaminationTypeAdmin,
    HarmfulFactorAdmin,
    MedicalSettingsAdmin,
    MedicalExaminationNormAdmin,
    EmployeeMedicalExaminationAdmin,
)
from .medical_referral import MedicalReferralAdmin
from .email_settings import EmailSettingsAdmin

__all__ = [
    'EquipmentAdmin',
    'KeyDeadlineCategoryAdmin',
    'MedicalExaminationTypeAdmin',
    'HarmfulFactorAdmin',
    'MedicalSettingsAdmin',
    'MedicalExaminationNormAdmin',
    'EmployeeMedicalExaminationAdmin',
    'MedicalReferralAdmin',
    'EmailSettingsAdmin',
]
