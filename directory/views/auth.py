from django.views.generic import CreateView
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache

from directory.forms.registration import CustomUserCreationForm
from directory.models import Organization

@method_decorator([sensitive_post_parameters(), csrf_protect, never_cache], name='dispatch')
class UserRegistrationView(CreateView):
    """🔐 Регистрация нового пользователя"""
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