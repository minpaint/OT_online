from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Охрана труда'

    def ready(self):
        """Импорт сигналов при загрузке приложения"""
        import core.signals