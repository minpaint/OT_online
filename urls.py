from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from directory.error_handlers import error_400, error_403, error_404, error_500
# Импортируем представление главной страницы
from directory.views.home import HomePageView  # убедитесь, что путь правильный!

urlpatterns = [
    # Изменено: вместо редиректа на /admin/ с корня, теперь главная страница обрабатывается HomePageView
    path('', HomePageView.as_view(), name='home'),

    # 👨‍💼 Админка Django
    path('admin/', admin.site.urls),

    # 📂 URL приложения directory (включая автодополнение)
    path('directory/', include('directory.urls', namespace='directory')),
]

# Настройки для режима разработки
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

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
