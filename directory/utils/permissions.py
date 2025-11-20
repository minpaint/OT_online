# directory/utils/permissions.py
"""
Централизованная система управления правами доступа (Scope-Based Access Control)

Иерархия доступа:
    Organization → StructuralSubdivision → Department

Принципы:
    1. Если дан доступ к Organization → доступ ко всем её Subdivisions и Departments
    2. Если дан доступ к Subdivision → доступ ко всем её Departments
    3. Если дан доступ к Department → доступ только к нему

Оптимизация:
    - Request-level cache (данные кешируются на время HTTP запроса)
    - Оптимизированные запросы (избежание N+1 проблемы)
"""

from django.db.models import Q


class AccessControlHelper:
    """
    Централизованная логика управления правами доступа.
    Все методы статические для удобства использования.
    """

    @staticmethod
    def get_accessible_organizations(user, request=None):
        """
        Возвращает QuerySet организаций, доступных пользователю.

        Логика:
        - Суперпользователь: все организации
        - Обычный: организации из profile.organizations + родительские организации
          из subdivisions и departments

        Args:
            user: объект User
            request: объект HttpRequest (для кеширования)

        Returns:
            QuerySet[Organization]
        """
        # Request-level cache
        if request and hasattr(request, '_user_orgs_cache'):
            return request._user_orgs_cache

        from directory.models import Organization

        if user.is_superuser:
            orgs = Organization.objects.all()
        elif not hasattr(user, 'profile'):
            orgs = Organization.objects.none()
        else:
            profile = user.profile

            # Оптимизированный запрос - один SELECT вместо множества
            orgs = Organization.objects.filter(
                Q(id__in=profile.organizations.values_list('id', flat=True)) |
                Q(subdivisions__in=profile.subdivisions.all()) |
                Q(departments__in=profile.departments.all())
            ).distinct()

        # Сохраняем в request-cache
        if request:
            request._user_orgs_cache = orgs

        return orgs

    @staticmethod
    def get_accessible_subdivisions(user, request=None):
        """
        Возвращает QuerySet подразделений, доступных пользователю.

        Логика:
        - Если доступ к Organization → все её subdivisions
        - Если доступ к Subdivision → это подразделение
        - Если доступ к Department → его subdivision (если есть)

        Args:
            user: объект User
            request: объект HttpRequest (для кеширования)

        Returns:
            QuerySet[StructuralSubdivision]
        """
        # Request-level cache
        if request and hasattr(request, '_user_subdivs_cache'):
            return request._user_subdivs_cache

        from directory.models import StructuralSubdivision

        if user.is_superuser:
            subdivs = StructuralSubdivision.objects.all()
        elif not hasattr(user, 'profile'):
            subdivs = StructuralSubdivision.objects.none()
        else:
            profile = user.profile

            # Оптимизированный запрос
            subdivs = StructuralSubdivision.objects.filter(
                Q(organization__in=profile.organizations.all()) |
                Q(id__in=profile.subdivisions.values_list('id', flat=True)) |
                Q(departments__in=profile.departments.all())
            ).distinct()

        # Сохраняем в request-cache
        if request:
            request._user_subdivs_cache = subdivs

        return subdivs

    @staticmethod
    def get_accessible_departments(user, request=None):
        """
        Возвращает QuerySet отделов, доступных пользователю.

        Логика:
        - Если доступ к Organization → все её departments
        - Если доступ к Subdivision → все её departments
        - Если доступ к Department → этот отдел

        Args:
            user: объект User
            request: объект HttpRequest (для кеширования)

        Returns:
            QuerySet[Department]
        """
        # Request-level cache
        if request and hasattr(request, '_user_depts_cache'):
            return request._user_depts_cache

        from directory.models import Department

        if user.is_superuser:
            depts = Department.objects.all()
        elif not hasattr(user, 'profile'):
            depts = Department.objects.none()
        else:
            profile = user.profile

            # Оптимизированный запрос
            depts = Department.objects.filter(
                Q(organization__in=profile.organizations.all()) |
                Q(subdivision__in=profile.subdivisions.all()) |
                Q(id__in=profile.departments.values_list('id', flat=True))
            ).distinct()

        # Сохраняем в request-cache
        if request:
            request._user_depts_cache = depts

        return depts

    @staticmethod
    def filter_queryset(queryset, user, request=None):
        """
        Универсальный фильтр для любого queryset по правам пользователя.

        Автоматически определяет поля organization/subdivision/department в модели
        и фильтрует по правам.

        Использование:
            qs = Equipment.objects.all()
            qs = AccessControlHelper.filter_queryset(qs, request.user, request)

        Args:
            queryset: QuerySet для фильтрации
            user: объект User
            request: объект HttpRequest (опционально, для кеширования)

        Returns:
            Отфильтрованный QuerySet
        """
        if user.is_superuser:
            return queryset

        if not hasattr(user, 'profile'):
            return queryset.none()

        model = queryset.model

        # Строим Q-объект для фильтрации
        q_filter = Q()

        # Проверяем наличие полей в модели
        has_org = hasattr(model, 'organization')
        has_subdiv = hasattr(model, 'subdivision')
        has_dept = hasattr(model, 'department')

        # Если в модели есть organization
        if has_org:
            accessible_orgs = AccessControlHelper.get_accessible_organizations(user, request)
            q_filter |= Q(organization__in=accessible_orgs)

        # Если в модели есть subdivision
        if has_subdiv:
            accessible_subdivs = AccessControlHelper.get_accessible_subdivisions(user, request)
            q_filter |= Q(subdivision__in=accessible_subdivs)

        # Если в модели есть department
        if has_dept:
            accessible_depts = AccessControlHelper.get_accessible_departments(user, request)
            q_filter |= Q(department__in=accessible_depts)

        # Если ни одного поля нет - возвращаем пустой queryset
        if not (has_org or has_subdiv or has_dept):
            return queryset.none()

        return queryset.filter(q_filter).distinct()

    @staticmethod
    def can_access_object(user, obj):
        """
        Проверяет, имеет ли пользователь доступ к конкретному объекту.

        Использование:
            equipment = Equipment.objects.get(pk=5)
            if AccessControlHelper.can_access_object(request.user, equipment):
                # доступ разрешен

        Args:
            user: объект User
            obj: объект для проверки

        Returns:
            bool: True если доступ разрешен
        """
        if user.is_superuser:
            return True

        if not hasattr(user, 'profile'):
            return False

        profile = user.profile

        # Проверяем organization
        if hasattr(obj, 'organization') and obj.organization:
            if obj.organization in profile.organizations.all():
                return True

        # Проверяем subdivision
        if hasattr(obj, 'subdivision') and obj.subdivision:
            # Прямой доступ к подразделению
            if obj.subdivision in profile.subdivisions.all():
                return True
            # Доступ через организацию
            if obj.subdivision.organization in profile.organizations.all():
                return True

        # Проверяем department
        if hasattr(obj, 'department') and obj.department:
            # Прямой доступ к отделу
            if obj.department in profile.departments.all():
                return True
            # Доступ через подразделение
            if obj.department.subdivision and obj.department.subdivision in profile.subdivisions.all():
                return True
            # Доступ через организацию
            if obj.department.organization in profile.organizations.all():
                return True

        return False

    @staticmethod
    def get_user_access_level(user):
        """
        Определяет уровень доступа пользователя.

        Возвращает:
            'superuser' - суперпользователь
            'organization' - доступ на уровне организации
            'subdivision' - доступ на уровне подразделения
            'department' - доступ на уровне отдела
            'none' - нет доступа

        Args:
            user: объект User

        Returns:
            str: уровень доступа
        """
        if user.is_superuser:
            return 'superuser'

        if not hasattr(user, 'profile'):
            return 'none'

        profile = user.profile

        if profile.organizations.exists():
            return 'organization'
        elif profile.subdivisions.exists():
            return 'subdivision'
        elif profile.departments.exists():
            return 'department'
        else:
            return 'none'
