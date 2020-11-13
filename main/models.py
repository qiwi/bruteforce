from main.mixins import EncryptedHashMixin, EncryptedPasswordMixin, AlphabetMixin
from django.contrib.postgres.fields import ArrayField
from django_celery_beat.models import PeriodicTask
from main.managers import HashQuerySet
from django.db import models


class DictionaryPeriodicTask(PeriodicTask):
    class Meta:
        proxy = True
        verbose_name = "Dictionary periodic task"
        verbose_name_plural = "⁣⁣⁣⁣Periodic tasks: ⁣⁣⁣Dictionary"


class BruteforcePeriodicTask(PeriodicTask):
    class Meta:
        proxy = True
        verbose_name = "Bruteforce periodic task"
        verbose_name_plural = "⁣⁣⁣⁣⁣⁣Periodic tasks: Bruteforce"


class OtherPeriodicTask(PeriodicTask):
    class Meta:
        proxy = True
        verbose_name = "Other periodic task"
        verbose_name_plural = "Periodic tasks: Other"


class Dictionary(models.Model):
    objects = models.Manager()
    name = models.CharField(max_length=100)
    path = models.TextField()
    file_size = models.BigIntegerField(default=0)
    word_count = models.BigIntegerField(default=0)

    class Meta:
        verbose_name = "Dictionary"
        verbose_name_plural = "Dictionaries"

    def __str__(self):
        return f"{self.name} {self.path}"


class Database(models.Model):
    objects = models.Manager()
    host = models.CharField(max_length=256)
    ip = ArrayField(models.GenericIPAddressField(), blank=True, null=True)
    port = models.IntegerField(default=None, null=True, blank=True)
    dsn = models.TextField(default="", null=True, blank=True)
    db_type = models.CharField(max_length=32)
    is_disabled = models.BooleanField(default=False)
    is_connected = models.BooleanField(default=True)
    is_pulled = models.BooleanField(default=True)
    last_connect_ts = models.DateTimeField(default=None, blank=True, null=True)
    last_pull_ts = models.DateTimeField(default=None, blank=True, null=True)
    last_check_success = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.host} {self.db_type}"


class BruteConfig(models.Model, AlphabetMixin):
    objects = models.Manager()
    name = models.CharField(max_length=100)
    min_length = models.PositiveSmallIntegerField(verbose_name="Минимальная длина")
    max_length = models.PositiveSmallIntegerField(verbose_name="Максимальная длина")
    digits = models.BooleanField(verbose_name="Цифры (0-9)              x10")
    upper_case_en = models.BooleanField(verbose_name="Английский (A-Z)  x26")
    lower_case_en = models.BooleanField(verbose_name="Английский (a-z)  x26")
    upper_case_ru = models.BooleanField(verbose_name="Русский (А-Я)     x33")
    lower_case_ru = models.BooleanField(verbose_name="Русский (а-я)     x33")
    symbols = models.BooleanField(verbose_name="Символы                 x33")
    custom_alphabet = models.TextField(
        blank=True, null=True, verbose_name="Свой алфавит"
    )

    def __str__(self):
        return self.name


class Hash(models.Model, EncryptedHashMixin, EncryptedPasswordMixin):
    objects = HashQuerySet.as_manager()
    database = models.ForeignKey(Database, on_delete=models.PROTECT)
    dictionary = models.ManyToManyField("main.Dictionary")
    brute_config = models.ManyToManyField("main.BruteConfig")
    login = models.CharField(max_length=256)
    created_ts = models.DateTimeField(auto_now_add=True)  # timestamp: when started
    hacked_ts = models.DateTimeField(null=True, blank=True)  # timestamp: when hacked
    cracking_started_ts = models.DateTimeField(
        null=True, blank=True
    )  # timestamp: last cracking start
    is_cracking = models.BooleanField(default=False)
    account_status = models.CharField(max_length=48, default="")
    is_changed = models.BooleanField(default=False)

    # !!! do NOT set/get fields directly, use .hash and .password properties from mixins !!!
    _encrypted_hash = models.TextField(null=True, blank=True, default=None)
    _encrypted_password = models.TextField(null=True, blank=True, default=None)

    class Meta:
        verbose_name = "Checked hash"
        verbose_name_plural = "Checked hashes"
