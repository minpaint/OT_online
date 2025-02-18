"""
🔀 Миксины для форм

Этот файл содержит базовый миксин для ограничения выборок по организациям.
Миксин OrganizationRestrictionFormMixin автоматически фильтрует поля формы,
связанные с организационной структурой, на основе разрешённых организаций,
указанных в профиле пользователя.
"""
from django import forms

class OrganizationRestrictionFormMixin:
    """
    🔒 Миксин для ограничения выборок по организациям, доступным пользователю.

    Применение:
      - Поле "organization" будет ограничено организациями из профиля пользователя. 🏢
      - Поля "subdivision", "department", "position", "documents" и "equipment" будут
        фильтроваться по organization, если такие поля есть в модели. 🔍
    """
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user and hasattr(self.user, 'profile'):
            allowed_orgs = self.user.profile.organizations.all()
            if 'organization' in self.fields:
                self.fields['organization'].queryset = allowed_orgs
                self.fields['organization'].help_text = "🏢 Выберите организацию из разрешённых"

            # Обратите внимание: здесь заменено 'document' на 'documents'
            for field_name in ['subdivision', 'department', 'position', 'documents', 'equipment']:
                if field_name in self.fields:
                    qs = self.fields[field_name].queryset
                    self.fields[field_name].queryset = qs.filter(organization__in=allowed_orgs)
                    self.fields[field_name].help_text = "🔍 Фильтрация по разрешённым организациям"
