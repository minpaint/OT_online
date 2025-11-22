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
        if request and hasattr(request, '_user_orgs_cache') and request._user_orgs_cache is not None:
            return request._user_orgs_cache

        from directory.models import Organization

        # Проверка на анонимного пользователя
        if not user or not user.is_authenticated:
            orgs = Organization.objects.none()
        elif user.is_superuser:
            orgs = Organization.objects.all()
        elif not hasattr(user, 'profile') or user.profile is None:
            orgs = Organization.objects.none()
        else:
            # Получаем организации из всех источников
            profile = user.profile

            # 1. Прямой доступ к организациям
            org_ids = set(profile.organizations.values_list('id', flat=True))

            # 2. Организации через подразделения
            org_ids.update(
                profile.subdivisions.values_list('organization_id', flat=True)
            )

            # 3. Организации через отделы
            org_ids.update(
                profile.departments.values_list('organization_id', flat=True)
            )

            orgs = Organization.objects.filter(id__in=org_ids)

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
        if request and hasattr(request, '_user_subdivs_cache') and request._user_subdivs_cache is not None:
            return request._user_subdivs_cache

        from directory.models import StructuralSubdivision

        # Проверка на анонимного пользователя
        if not user or not user.is_authenticated:
            subdivs = StructuralSubdivision.objects.none()
        elif user.is_superuser:
            subdivs = StructuralSubdivision.objects.all()
        elif not hasattr(user, 'profile') or user.profile is None:
            subdivs = StructuralSubdivision.objects.none()
        else:
            # Получаем подразделения из всех источников
            profile = user.profile

            # 1. Все подразделения доступных организаций
            subdivs_from_orgs = StructuralSubdivision.objects.filter(
                organization__in=profile.organizations.all()
            )

            # 2. Прямой доступ к подразделениям
            direct_subdivs = profile.subdivisions.all()

            # 3. Подразделения через отделы
            subdivs_from_depts = StructuralSubdivision.objects.filter(
                id__in=profile.departments.values_list('subdivision_id', flat=True)
            )

            # Объединяем все источники
            subdivs = (subdivs_from_orgs | direct_subdivs | subdivs_from_depts).distinct()

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
        if request and hasattr(request, '_user_depts_cache') and request._user_depts_cache is not None:
            return request._user_depts_cache

        from directory.models import Department

        # Проверка на анонимного пользователя
        if not user or not user.is_authenticated:
            depts = Department.objects.none()
        elif user.is_superuser:
            depts = Department.objects.all()
        elif not hasattr(user, 'profile') or user.profile is None:
            depts = Department.objects.none()
        else:
            # Получаем отделы из всех источников
            profile = user.profile

            # 1. Все отделы доступных организаций
            depts_from_orgs = Department.objects.filter(
                organization__in=profile.organizations.all()
            )

            # 2. Все отделы доступных подразделений
            depts_from_subdivs = Department.objects.filter(
                subdivision__in=profile.subdivisions.all()
            )

            # 3. Прямой доступ к отделам
            direct_depts = profile.departments.all()

            # Объединяем все источники
            depts = (depts_from_orgs | depts_from_subdivs | direct_depts).distinct()

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

        # Проверяем наличие полей в модели через _meta (правильный способ)
        field_names = [f.name for f in model._meta.get_fields()]
        has_org = 'organization' in field_names
        has_subdiv = 'subdivision' in field_names
        has_dept = 'department' in field_names

        # Если ни одного поля нет - возвращаем пустой queryset
        if not (has_org or has_subdiv or has_dept):
            return queryset.none()

        # Получаем доступные объекты
        accessible_orgs = AccessControlHelper.get_accessible_organizations(user, request) if has_org else []
        accessible_subdivs = AccessControlHelper.get_accessible_subdivisions(user, request) if has_subdiv else []
        # Отделы нужны и для моделей без поля department (например, Department)
        # поэтому запрашиваем их без привязки к has_dept
        accessible_depts = AccessControlHelper.get_accessible_departments(user, request)
        # Признак: у пользователя есть прямое закрепление ТОЛЬКО за отделами
        # (без доступа к целым организациям или подразделениям)
        direct_dept_user = (
            hasattr(user, 'profile') and
            user.profile.departments.exists() and
            not user.profile.organizations.exists() and
            not user.profile.subdivisions.exists()
        )

        # Для пользователей, привязанных напрямую к отделам:
        # 1) список отделов – ровно их own departments
        # 2) для моделей с полем department – фильтруем только по ним, без отката на подразделение/организацию
        # 3) НЕ показываем сотрудников подразделения без конкретного отдела
        if direct_dept_user:
            # Специальный случай: сама модель Department
            if model._meta.model_name == 'department':
                return queryset.filter(id__in=accessible_depts).distinct()
            # Для моделей с полем department - СТРОГО только сотрудники с заполненным department
            if has_dept:
                return queryset.filter(
                    department__isnull=False,  # ВАЖНО: только с заполненным отделом
                    department__in=accessible_depts
                ).distinct()

        # Строим фильтр с приоритетом: department > subdivision > organization
        # Логика: фильтруем по САМОМУ КОНКРЕТНОМУ заполненному полю
        q_filter = Q()

        if has_dept and has_subdiv and has_org:
            # Есть все три поля - фильтруем по приоритету
            q_filter = (
                # Если department заполнен, проверяем его
                Q(department__isnull=False, department__in=accessible_depts) |
                # Иначе если subdivision заполнен, проверяем его
                Q(department__isnull=True, subdivision__isnull=False, subdivision__in=accessible_subdivs) |
                # Иначе проверяем organization
                Q(department__isnull=True, subdivision__isnull=True, organization__in=accessible_orgs)
            )
        elif has_subdiv and has_org:
            # Есть subdivision и organization
            q_filter = (
                Q(subdivision__isnull=False, subdivision__in=accessible_subdivs) |
                Q(subdivision__isnull=True, organization__in=accessible_orgs)
            )
        elif has_dept and has_org:
            # Есть department и organization (без subdivision)
            q_filter = (
                Q(department__isnull=False, department__in=accessible_depts) |
                Q(department__isnull=True, organization__in=accessible_orgs)
            )
        elif has_org:
            # Только organization
            q_filter = Q(organization__in=accessible_orgs)
        elif has_subdiv:
            # Только subdivision
            q_filter = Q(subdivision__in=accessible_subdivs)
        elif has_dept:
            # Только department
            q_filter = Q(department__in=accessible_depts)

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
