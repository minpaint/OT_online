from django.views.generic import CreateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters

from .models import (
    Position,
    Organization,
    StructuralSubdivision,
    Department,
    Employee
)
from .forms.registration import CustomUserCreationForm


class HomeView(ListView):
    """🏠 Главная страница системы"""
    template_name = 'directory/home.html'
    model = Organization

    def get_context_data(self, **kwargs):
        """📊 Получение статистики для главной страницы"""
        context = super().get_context_data(**kwargs)
        context.update({
            'total_employees': Employee.objects.count(),  # 👥 Всего сотрудников
            'total_positions': Position.objects.count(),  # 👔 Всего должностей
            'total_organizations': Organization.objects.count(),  # 🏢 Всего организаций
            'total_subdivisions': StructuralSubdivision.objects.count(),  # 🏭 Всего подразделений
        })
        return context


class EmployeeListView(LoginRequiredMixin, ListView):
    """👥 Список сотрудников"""
    model = Employee
    template_name = 'directory/employees/list.html'
    context_object_name = 'employees'
    paginate_by = 20

    def get_queryset(self):
        """🔍 Получение отфильтрованного списка сотрудников"""
        queryset = (
            Employee.objects
            .select_related('subdivision', 'position', 'organization', 'department')
            .order_by('full_name_nominative')
        )

        if organization_id := self.request.GET.get('organization'):
            queryset = queryset.filter(organization_id=organization_id)
        if subdivision_id := self.request.GET.get('subdivision'):
            queryset = queryset.filter(subdivision_id=subdivision_id)
        return queryset

    def get_context_data(self, **kwargs):
        """📋 Дополнительные данные для шаблона"""
        context = super().get_context_data(**kwargs)
        context.update({
            'organizations': Organization.objects.all(),  # 🏢 Организации
            'subdivisions': StructuralSubdivision.objects.all(),  # 🏭 Подразделения
            'selected_organization': self.request.GET.get('organization'),
            'selected_subdivision': self.request.GET.get('subdivision'),
        })
        return context


class EmployeeCreateView(LoginRequiredMixin, CreateView):
    """👤 Создание нового сотрудника"""
    model = Employee
    template_name = 'directory/employees/form.html'
    success_url = reverse_lazy('directory:employee_list')
    fields = [
        'full_name_nominative',  # 📝 ФИО в именительном падеже
        'full_name_dative',  # 📝 ФИО в дательном падеже
        'organization',  # 🏢 Организация
        'subdivision',  # 🏭 Подразделение
        'department',  # 📂 Отдел
        'position',  # 👔 Должность
        'is_contractor',  # 📄 Договор подряда
        'date_of_birth',  # 📅 Дата рождения
        'place_of_residence',  # 🏠 Место проживания
        'height',  # 📏 Рост
        'clothing_size',  # 👕 Размер одежды
        'shoe_size'  # 👞 Размер обуви
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('➕ Добавление сотрудника')
        return context


@method_decorator([sensitive_post_parameters(), csrf_protect, never_cache], name='dispatch')
class UserRegistrationView(CreateView):
    """🔐 Регистрация нового пользователя с выбором организаций"""
    form_class = CustomUserCreationForm
    template_name = 'directory/registration/register.html'
    success_url = reverse_lazy('directory:home')

    def get_context_data(self, **kwargs):
        """📋 Контекст для шаблона регистрации"""
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('✨ Регистрация нового пользователя'),
            'organizations': Organization.objects.all().order_by('full_name_ru'),
        })
        return context

    def form_valid(self, form):
        """✅ Обработка успешной валидации формы"""
        try:
            user = form.save()
            login(self.request, user)
            messages.success(
                self.request,
                _("🎉 Регистрация прошла успешно! Добро пожаловать, %(username)s!") % {
                    'username': user.get_full_name() or user.username
                }
            )
            return redirect(self.success_url)
        except Exception as e:
            messages.error(
                self.request,
                _("❌ Произошла ошибка при регистрации. Пожалуйста, попробуйте позже.")
            )
            return self.form_invalid(form)

    def form_invalid(self, form):
        """❌ Обработка ошибок валидации формы"""
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(
                    self.request,
                    f"⚠️ {form.fields[field].label}: {error}"
                )
        return render(
            self.request,
            self.template_name,
            self.get_context_data(form=form)
        )

    def dispatch(self, request, *args, **kwargs):
        """🔍 Проверка статуса аутентификации"""
        if request.user.is_authenticated:
            messages.info(request, _("ℹ️ Вы уже авторизованы в системе."))
            return redirect('directory:home')
        return super().dispatch(request, *args, **kwargs)


@login_required
@never_cache
def get_subdivisions(request):
    """🏭 Получение списка подразделений по организации"""
    organization_id = request.GET.get('organization')
    subdivisions = (
        StructuralSubdivision.objects
        .filter(organization_id=organization_id)
        .order_by('name')
        .values('id', 'name')
    )
    return JsonResponse(list(subdivisions), safe=False)


@login_required
@never_cache
def get_positions(request):
    """👔 Получение списка должностей по подразделению"""
    subdivision_id = request.GET.get('subdivision')
    positions = (
        Position.objects
        .filter(subdivision_id=subdivision_id)
        .order_by('position_name')
        .values('id', 'position_name')
    )
    return JsonResponse(list(positions), safe=False)


@login_required
@never_cache
def get_departments(request):
    """📂 Получение списка отделов по подразделению"""
    subdivision_id = request.GET.get('subdivision')
    departments = (
        Department.objects
        .filter(subdivision_id=subdivision_id)
        .order_by('name')
        .values('id', 'name')
    )
    return JsonResponse(list(departments), safe=False)