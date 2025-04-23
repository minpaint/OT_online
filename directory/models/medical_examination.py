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

    examination_type = models.ForeignKey(
        MedicalExaminationType,
        on_delete=models.PROTECT,
        related_name="harmful_factors",
        verbose_name="Вид медосмотра",
        help_text="Вид медосмотра, который требуется для данного вредного фактора"
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
        unique_together = [['short_name', 'examination_type']]

    def __str__(self):
        return f"{self.short_name} - {self.full_name}"


class MedicalSettings(models.Model):
    """
    ⚙️ Настройки для модуля медосмотров.

    Хранит параметры, влияющие на работу системы управления медосмотрами.
    """
    days_before_issue = models.PositiveIntegerField(
        default=30,
        verbose_name="Дней до выдачи направления",
        help_text="За сколько дней до окончания срока менять статус на 'Нужно выдать направление'"
    )

    days_before_email = models.PositiveIntegerField(
        default=45,
        verbose_name="Дней до уведомления по email",
        help_text="За сколько дней до окончания срока отправлять email-уведомление"
    )

    class Meta:
        verbose_name = "Настройки медосмотров"
        verbose_name_plural = "Настройки медосмотров"

    def __str__(self):
        return "Настройки медосмотров"

    @classmethod
    def get_settings(cls):
        """Получает настройки или создает с дефолтными значениями"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings