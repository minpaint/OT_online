from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from directory.error_handlers import error_400, error_403, error_404, error_500
# Импортируем представление главной страницы
from directory.views.home import HomePageView


urlpatterns = [
    # Изменено: вместо редиректа на /admin/ с корня, теперь главная страница обрабатывается HomePageView
    path('', HomePageView.as_view(), name='home'),

    # 👨‍💼 Админка Django
    path('admin/', admin.site.urls),

    # 📂 URL приложения directory (включая автодополнение)
    # Ключевое исправление - указываем непосредственно модуль, а не строку
    path('directory/', include('directory.urls')),

    # ⏰ URL приложения deadline_control (Контроль сроков)
    path('deadline-control/', include('deadline_control.urls')),
]

# Обслуживание media файлов для ВСЕХ доменов (включая exam.localhost)
# ВАЖНО: В продакшене используйте nginx/apache для обслуживания media
if settings.DEBUG:
    # Явно добавляем serve view для media файлов
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {
            'document_root': settings.MEDIA_ROOT,
        }),
    ]
else:
    # Для продакшена используем static helper
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Настройки для режима разработки
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns.append(path('__debug__/', include(debug_toolbar.urls)))

# Кастомизация админки
admin.site.site_header = '🏢 Система управления ОТ'
admin.site.site_title = '🎛️ Панель управления'
admin.site.index_title = '⚙️ Управление системой'

# Обработчики ошибок
handler400 = error_400
handler403 = error_403
handler404 = error_404
handler500 = error_500