# deadline_control/models/email_settings.py

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


class EmailSettings(models.Model):
    """
    📧 Настройки SMTP для отправки email-уведомлений.

    Позволяет настроить параметры подключения к почтовому серверу
    для отправки уведомлений о медосмотрах и других событиях.
    """

    organization = models.OneToOneField(
        'directory.Organization',
        on_delete=models.CASCADE,
        verbose_name="Организация",
        help_text="Организация, для которой применяются настройки email",
        related_name='email_settings'
    )

    # SMTP настройки
    email_backend = models.CharField(
        max_length=255,
        default='django.core.mail.backends.smtp.EmailBackend',
        verbose_name="Email Backend",
        help_text="Бэкенд для отправки email (обычно не требует изменения)"
    )

    email_host = models.CharField(
        max_length=255,
        verbose_name="SMTP сервер",
        help_text="Адрес SMTP сервера (например: smtp.gmail.com, smtp.yandex.ru)",
        blank=True,
        default=''
    )

    email_port = models.PositiveIntegerField(
        default=587,
        validators=[MinValueValidator(1), MaxValueValidator(65535)],
        verbose_name="SMTP порт",
        help_text="Порт SMTP сервера (587 для TLS, 465 для SSL, 25 для обычного)"
    )

    email_use_tls = models.BooleanField(
        default=True,
        verbose_name="Использовать TLS",
        help_text="Использовать TLS шифрование (рекомендуется для порта 587)"
    )

    email_use_ssl = models.BooleanField(
        default=False,
        verbose_name="Использовать SSL",
        help_text="Использовать SSL шифрование (для порта 465)"
    )

    email_host_user = models.CharField(
        max_length=255,
        verbose_name="Email пользователь",
        help_text="Email адрес для отправки (логин на SMTP сервере)",
        blank=True,
        default=''
    )

    email_host_password = models.CharField(
        max_length=255,
        verbose_name="Пароль",
        help_text="Пароль от email (для Gmail - пароль приложения)",
        blank=True,
        default=''
    )

    default_from_email = models.EmailField(
        verbose_name="Email отправителя",
        help_text="Email адрес, который будет указан в поле 'От кого'",
        blank=True,
        default=''
    )

    # Настройки уведомлений
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активно",
        help_text="Включить отправку email для этой организации"
    )

    recipient_emails = models.TextField(
        verbose_name="Email получателей",
        help_text="Email адреса получателей уведомлений (по одному на строку)",
        blank=True,
        default=''
    )

    # Метаданные
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата изменения"
    )

    class Meta:
        verbose_name = "Настройки Email (SMTP)"
        verbose_name_plural = "Настройки Email (SMTP)"
        ordering = ['organization__short_name_ru']

    def __str__(self):
        return f"Email настройки - {self.organization.short_name_ru}"

    def clean(self):
        """Валидация настроек"""
        super().clean()

        # Проверка: TLS и SSL не могут быть включены одновременно
        if self.email_use_tls and self.email_use_ssl:
            raise ValidationError({
                'email_use_tls': 'TLS и SSL не могут быть включены одновременно',
                'email_use_ssl': 'TLS и SSL не могут быть включены одновременно',
            })

        # Если указан хост, требуем заполнить пользователя
        if self.email_host and not self.email_host_user:
            raise ValidationError({
                'email_host_user': 'Укажите email пользователя для SMTP сервера'
            })

        # Если указан пользователь, требуем пароль
        if self.email_host_user and not self.email_host_password:
            raise ValidationError({
                'email_host_password': 'Укажите пароль для SMTP сервера'
            })

    def get_recipient_list(self):
        """
        Возвращает список email адресов получателей.
        Парсит текстовое поле recipient_emails.
        """
        if not self.recipient_emails:
            return []

        # Разделяем по строкам и удаляем пробелы
        emails = [
            email.strip()
            for email in self.recipient_emails.strip().split('\n')
            if email.strip()
        ]
        return emails

    def get_connection(self):
        """
        Возвращает Django email connection с настройками этой организации.
        Используется для отправки email с кастомными SMTP параметрами.
        """
        from django.core.mail import get_connection

        if not self.is_active or not self.email_host:
            return None

        return get_connection(
            backend=self.email_backend,
            host=self.email_host,
            port=self.email_port,
            username=self.email_host_user,
            password=self.email_host_password,
            use_tls=self.email_use_tls,
            use_ssl=self.email_use_ssl,
            fail_silently=False,
        )

    @classmethod
    def get_settings(cls, organization):
        """
        Возвращает настройки email для указанной организации.
        Создает новые настройки с дефолтными значениями, если их еще нет.
        """
        settings, created = cls.objects.get_or_create(
            organization=organization,
            defaults={
                'is_active': False,  # По умолчанию выключено до настройки
                'email_backend': 'django.core.mail.backends.smtp.EmailBackend',
                'email_port': 587,
                'email_use_tls': True,
                'email_use_ssl': False,
            }
        )
        return settings
