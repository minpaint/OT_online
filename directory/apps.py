from django.apps import AppConfig

class DirectoryConfig(AppConfig):
    """
    📦 Конфигурация приложения "directory" (Справочники).
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'directory'
    verbose_name = 'Справочники'

    def ready(self):
        """
        Импортируем signals при инициализации приложения.
        """
        import directory.signals  # noqa: F401
