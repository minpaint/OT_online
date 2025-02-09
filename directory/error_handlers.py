# 📁 directory/error_handlers.py

from django.shortcuts import render

def error_400(request, exception):
    """🔍 Обработчик ошибки 400 - Некорректный запрос"""
    context = {
        'error_code': '400',
        'error_message': 'Некорректный запрос',
        'error_details': str(exception) if exception else None
    }
    return render(request, 'errors/400.html', context, status=400)

def error_403(request, exception):
    """🔒 Обработчик ошибки 403 - Доступ запрещен"""
    context = {
        'error_code': '403',
        'error_message': 'Доступ запрещен',
        'error_details': str(exception) if exception else None
    }
    return render(request, 'errors/403.html', context, status=403)

def error_404(request, exception):
    """🔍 Обработчик ошибки 404 - Страница не найдена"""
    context = {
        'error_code': '404',
        'error_message': 'Страница не найдена',
        'error_details': str(exception) if exception else None
    }
    return render(request, 'errors/404.html', context, status=404)

def error_500(request):
    """⚠️ Обработчик ошибки 500 - Внутренняя ошибка сервера"""
    context = {
        'error_code': '500',
        'error_message': 'Внутренняя ошибка сервера'
    }
    return render(request, 'errors/500.html', context, status=500)