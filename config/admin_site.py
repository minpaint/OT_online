# config/admin_site.py

from collections import OrderedDict
from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _

class OTAdminSite(AdminSite):
    site_header = "OT-online Администрирование"
    site_title = "OT-online"
    index_title = "Панель управления"

    MENU_ORDER = OrderedDict([
        (_("🔑 Администрирование доступа"), [
            "User", "Group",
        ]),
        (_("🏢 Организация"), [
            "Organization", "Subdivision", "Department", "StructuralSubdivision",
        ]),
        (_("👥 Сотрудники и должности"), [
            "Position", "Employee",
        ]),
        (_("🏥 Медосмотры"), [
            "MedicalExaminationType",
            "HarmfulFactor",
            "PositionMedicalFactor",
            "EmployeeMedicalExamination",
            "MedicalExaminationNorm",
            "MedicalSettings",
        ]),
        (_("🛡️ СИЗ"), [
            "SIZ", "SIZNorm",
        ]),
        (_("📄 Документы и шаблоны"), [
            "DocumentTemplate", "Document", "Equipment",
        ]),
        (_("📑 Прием на работу"), [
            "EmployeeHiring", "Commission", "GeneratedDocument",
        ]),
    ])

    def get_app_list(self, request):
        """
        Возвращает меню, сгруппированное по логическим блокам.
        """
        app_list = super().get_app_list(request)

        # Плоский список всех моделей
        all_models = []
        for app in app_list:
            all_models.extend(app['models'])

        # Распределение по группам
        grouped_apps = OrderedDict()
        for section, models in self.MENU_ORDER.items():
            grouped_apps[section] = {'name': section, 'models': []}
            for model in models:
                for m in all_models:
                    if m['object_name'] == model:
                        grouped_apps[section]['models'].append(m)

        # Прочее
        grouped_apps["Прочее"] = {'name': "Прочее", 'models': []}
        for m in all_models:
            if not any(m['object_name'] in models for models in self.MENU_ORDER.values()):
                grouped_apps["Прочее"]['models'].append(m)

        return [section for section in grouped_apps.values() if section['models']]
