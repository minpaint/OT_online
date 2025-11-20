# directory/mixins.py
"""
Mixins для автоматической фильтрации views по правам доступа.

Использование:
    class EquipmentListView(LoginRequiredMixin, AccessControlMixin, ListView):
        model = Equipment
        # Фильтрация происходит автоматически!

    class EquipmentUpdateView(LoginRequiredMixin, AccessControlObjectMixin, UpdateView):
        model = Equipment
        # Проверка прав доступа к объекту происходит автоматически!
"""

from django.core.exceptions import PermissionDenied
from directory.utils.permissions import AccessControlHelper


class AccessControlMixin:
    """
    Mixin для автоматической фильтрации queryset по правам доступа пользователя.

    Используется в ListView для фильтрации списка объектов.
    Автоматически применяет фильтр на основе прав пользователя (organizations/subdivisions/departments).

    Атрибуты:
        skip_access_control (bool): Если True, пропускает фильтрацию (по умолчанию False)

    Примеры:
        # Базовое использование
        class EquipmentListView(LoginRequiredMixin, AccessControlMixin, ListView):
            model = Equipment

        # С дополнительной фильтрацией
        class ActiveEquipmentListView(LoginRequiredMixin, AccessControlMixin, ListView):
            model = Equipment

            def get_queryset(self):
                qs = super().get_queryset()  # Уже отфильтровано по правам!
                return qs.filter(is_active=True)  # Добавляем свои фильтры

        # Отключение фильтрации (для суперпользователей)
        class AllEquipmentListView(LoginRequiredMixin, AccessControlMixin, ListView):
            model = Equipment
            skip_access_control = True
    """

    skip_access_control = False

    def get_queryset(self):
        """
        Возвращает queryset, автоматически отфильтрованный по правам пользователя.
        """
        qs = super().get_queryset()

        # Пропускаем фильтрацию если установлен флаг
        if self.skip_access_control:
            return qs

        # Применяем фильтр прав доступа
        return AccessControlHelper.filter_queryset(qs, self.request.user, self.request)


class AccessControlObjectMixin:
    """
    Mixin для проверки прав доступа к конкретному объекту.

    Используется в DetailView, UpdateView, DeleteView для проверки прав доступа
    к редактируемому/удаляемому/просматриваемому объекту.

    Выбрасывает PermissionDenied если у пользователя нет доступа к объекту.

    Атрибуты:
        skip_access_control (bool): Если True, пропускает проверку (по умолчанию False)

    Примеры:
        # Базовое использование
        class EquipmentUpdateView(LoginRequiredMixin, AccessControlObjectMixin, UpdateView):
            model = Equipment
            # Если пользователь пытается редактировать оборудование другой организации,
            # будет выброшено PermissionDenied (403)

        class EquipmentDetailView(LoginRequiredMixin, AccessControlObjectMixin, DetailView):
            model = Equipment

        class EquipmentDeleteView(LoginRequiredMixin, AccessControlObjectMixin, DeleteView):
            model = Equipment

        # Отключение проверки
        class AdminEquipmentUpdateView(LoginRequiredMixin, AccessControlObjectMixin, UpdateView):
            model = Equipment
            skip_access_control = True
    """

    skip_access_control = False

    def get_object(self, queryset=None):
        """
        Возвращает объект, предварительно проверив права доступа к нему.

        Raises:
            PermissionDenied: Если у пользователя нет доступа к объекту
        """
        obj = super().get_object(queryset)

        # Пропускаем проверку если установлен флаг
        if self.skip_access_control:
            return obj

        # Проверяем права доступа
        if not AccessControlHelper.can_access_object(self.request.user, obj):
            raise PermissionDenied("У вас нет доступа к этому объекту")

        return obj


class AccessControlCombinedMixin(AccessControlMixin, AccessControlObjectMixin):
    """
    Комбинированный mixin для фильтрации queryset И проверки прав доступа к объекту.

    Удобен для views, которые работают и со списком, и с отдельными объектами
    (например, некоторые CreateView с предзаполнением на основе других объектов).

    Примеры:
        class EquipmentCloneView(LoginRequiredMixin, AccessControlCombinedMixin, CreateView):
            model = Equipment

            def get_initial(self):
                # Получаем исходное оборудование для клонирования
                # Права доступа проверятся автоматически
                source = self.get_object()
                return {'name': f"Копия {source.name}"}
    """
    pass
