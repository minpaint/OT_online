from django.db import models
from django.core.validators import MinValueValidator, FileExtensionValidator
from django.utils import timezone


class MedicalExaminationType(models.Model):
    """
    🏥 Справочник видов медицинских осмотров.

    Хранит информацию о различных видах медосмотров, которые могут проводиться
    (например, предварительный, периодический, внеочередной и т.д.)
    """
    name = models.CharField(
        max_length=255,
        verbose_name="Название",
        unique=True,
        help_text="Название вида медицинского осмотра"
    )

    class Meta:
        verbose_name = "Вид медицинского осмотра"
        verbose_name_plural = "Виды медицинских осмотров"
        ordering = ['name']

    def __str__(self):
        return self.name


class HarmfulFactor(models.Model):
    """
    ☢️ Справочник вредных производственных факторов.

    Хранит информацию о факторах производственной среды, влияющих на
    необходимость прохождения медицинских осмотров.
    """
    short_name = models.CharField(
        max_length=50,
        verbose_name="Сокращенное наименование",
        help_text="Краткое кодовое обозначение вредного фактора"
    )

    full_name = models.CharField(
        max_length=255,
        verbose_name="Полное наименование",
        help_text="Полное наименование вредного производственного фактора"
    )

    periodicity = models.PositiveIntegerField(
        verbose_name="Периодичность (месяцы)",
        validators=[MinValueValidator(1)],
        help_text="Периодичность проведения медосмотра в месяцах"
    )

    class Meta:
        verbose_name = "Вредный фактор"
        verbose_name_plural = "Вредные факторы"
        ordering = ['short_name']
        unique_together = [['short_name']]

    def __str__(self):
        return self.short_name


class MedicalSettings(models.Model):
    """
    Настройки уведомлений для контроля сроков медосмотров.
    Каждая организация имеет свои настройки.
    """
    organization = models.OneToOneField(
        'directory.Organization',
        on_delete=models.CASCADE,
        verbose_name="Организация",
        help_text="Организация, для которой применяются настройки",
        null=True,  # Временно nullable для миграции
        blank=True
    )

    days_before_issue = models.PositiveIntegerField(
        default=30,
        verbose_name="Дней до отметки к выдаче",
        help_text="Через сколько дней до наступления срока выводить статус 'к выдаче'"
    )

    days_before_email = models.PositiveIntegerField(
        default=45,
        verbose_name="Дней до напоминания на email",
        help_text="За сколько дней до наступления срока отправлять email-уведомление"
    )

    referral_template = models.FileField(
        upload_to='document_templates/medical/',
        verbose_name="Шаблон направления (необязательно)",
        blank=True,
        null=True,
        help_text="Загрузите свой DOCX шаблон, если хотите использовать его вместо эталонного. "
                  "Если не указан - будет использоваться эталонный шаблон системы."
    )

    class Meta:
        verbose_name = "Настройки медосмотров"
        verbose_name_plural = "Настройки медосмотров"
        ordering = ['organization__short_name_ru']

    def __str__(self):
        return f"Настройки медосмотров - {self.organization.short_name_ru}"

    @classmethod
    def get_settings(cls, organization):
        """
        Возвращает настройки для указанной организации.
        Создает новые настройки с дефолтными значениями, если их еще нет.
        """
        settings, created = cls.objects.get_or_create(
            organization=organization,
            defaults={
                'days_before_issue': 30,
                'days_before_email': 45,
            }
        )
        return settings

