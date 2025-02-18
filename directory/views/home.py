from django.views.generic import FormView
from django.urls import reverse_lazy
from django.contrib import messages
from directory.forms.employee_hiring import EmployeeHiringForm


class EmployeeHiringView(FormView):
    """
    📝 Форма для приема на работу (главная страница).

    Эта форма позволяет добавить сотрудника с выбором организации, подразделения,
    отдела и должности. Форма получает текущего пользователя через get_form_kwargs,
    чтобы выпадающие списки фильтровались по организациям, закрепленным в профиле.
    """
    template_name = 'directory/home.html'
    form_class = EmployeeHiringForm
    success_url = reverse_lazy('directory:home')

    def get_form_kwargs(self):
        """
        🔑 Добавляем request.user в kwargs для EmployeeHiringForm.
        Это нужно для работы миксина OrganizationRestrictionFormMixin
        и динамической фильтрации зависимых полей.
        """
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        """
        💾 Если форма прошла валидацию, сохраняем данные и выводим сообщение об успехе.
        Здесь можно добавить логику предпросмотра, если требуется.
        """
        form.save()
        messages.success(self.request, "Сотрудник успешно принят на работу!")
        return super().form_valid(form)
