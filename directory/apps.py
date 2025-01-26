from django.apps import AppConfig

class DirectoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'directory'
    verbose_name = 'Справочники'

    def ready(self):
        """Импорт сигналов при загрузке приложения."""
        import directory.signals  # будем создавать позже, если потребуется
