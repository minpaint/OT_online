from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # 👨‍💼 Админка
    path('admin/', admin.site.urls),

    # 🔗 Smart Selects - главное подключение
    re_path(r'^chaining/', include('smart_selects.urls')),  # Используем re_path вместо path

    # 📁 Приложение directory
    path('directory/', include(('directory.urls', 'directory'), namespace='directory')),
]

# 🛠️ Настройки для режима разработки
if settings.DEBUG:
    # 🐞 Debug Toolbar
    import debug_toolbar

    urlpatterns = [
                      path('__debug__/', include(debug_toolbar.urls)),  # Упрощенное подключение Debug Toolbar
                  ] + urlpatterns

    # 📂 Статические и медиа файлы
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)