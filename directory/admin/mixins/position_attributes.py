import logging

from directory.models.siz import SIZNorm
from deadline_control.models.medical_norm import MedicalExaminationNorm

logger = logging.getLogger(__name__)

class PositionAttributesMixin:
    """
    Миксин для проверки атрибутов должностей:
    СИЗ, мед.факторов, электробезопасности и т.п.
    (Убрано всё, что было про commission_role)
    """

    def check_siz_norms(self, position):
        try:
            if hasattr(position, 'siz_norms') and position.siz_norms.exists():
                return True
            return SIZNorm.objects.filter(
                position__position_name__iexact=position.position_name,
                siz__isnull=False
            ).exists()
        except Exception as e:
            logger.error(f"Ошибка при проверке норм СИЗ: {e}")
            return False

    def has_overridden_siz_norms(self, position):
        try:
            return hasattr(position, 'siz_norms') and position.siz_norms.exists()
        except Exception as e:
            logger.error(f"Ошибка при проверке собственных норм СИЗ: {e}")
            return False

    def has_reference_siz_norms(self, position):
        try:
            return SIZNorm.objects.filter(
                position__position_name__iexact=position.position_name,
                siz__isnull=False
            ).exists()
        except Exception as e:
            logger.error(f"Ошибка при проверке эталонных норм СИЗ: {e}")
            return False

    def check_medical_factors(self, position):
        try:
            if hasattr(position, 'medical_factors') and position.medical_factors.filter(is_disabled=False).exists():
                return True
            return MedicalExaminationNorm.objects.filter(
                position_name__iexact=position.position_name
            ).exists()
        except Exception as e:
            logger.error(f"Ошибка при проверке медицинских факторов: {e}")
            return False

    def has_overridden_medical_factors(self, position):
        try:
            return hasattr(position, 'medical_factors') and position.medical_factors.filter(is_disabled=False).exists()
        except Exception as e:
            logger.error(f"Ошибка при проверке собственных мед. факторов: {e}")
            return False

    def has_reference_medical_factors(self, position):
        try:
            return MedicalExaminationNorm.objects.filter(
                position_name__iexact=position.position_name
            ).exists()
        except Exception as e:
            logger.error(f"Ошибка при проверке эталонных мед. факторов: {e}")
            return False

    def get_position_attributes(self, position):
        """
        Собирает все флаги-атрибуты по должности.
        Поля про commission_role удалены.
        """
        return {
            'is_responsible_for_safety': position.is_responsible_for_safety,
            'is_electrical_personnel': position.is_electrical_personnel,
            'can_be_internship_leader': position.can_be_internship_leader,
            'can_sign_orders': position.can_sign_orders,
            'electrical_group': position.electrical_safety_group,
            'has_siz_norms': self.check_siz_norms(position),
            'has_overridden_siz_norms': self.has_overridden_siz_norms(position),
            'has_reference_siz': self.has_reference_siz_norms(position),
            'has_medical_factors': self.check_medical_factors(position),
            'has_overridden_medical_factors': self.has_overridden_medical_factors(position),
            'has_reference_medical': self.has_reference_medical_factors(position),
        }

    def enrich_tree_with_position_attributes(self, tree):
        for org_data in tree.values():
            for item in org_data['items']:
                self.enrich_item_with_position_attributes(item)
            for sub_data in org_data['subdivisions'].values():
                for item in sub_data['items']:
                    self.enrich_item_with_position_attributes(item)
                for dept_data in sub_data['departments'].values():
                    for item in dept_data['items']:
                        self.enrich_item_with_position_attributes(item)
        return tree

    def enrich_item_with_position_attributes(self, item):
        # Должен быть переопределён в конкретных миксинах (Position, Employee)
        pass
