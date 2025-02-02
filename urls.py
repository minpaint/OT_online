from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('smart-selects/', include('smart_selects.urls')),
    path('directory/', include('directory.urls', namespace='directory')),
    path('admin/', admin.site.urls),
    path('chaining/', include('smart_selects.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
