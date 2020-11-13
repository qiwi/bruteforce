from main.models import Hash, DictionaryPeriodicTask, BruteforcePeriodicTask
from main.models import Dictionary, BruteConfig, Database
from main.models import OtherPeriodicTask
from main.forms import DictionaryPeriodicTaskForm, BruteforcePeriodicTaskForm
from main.forms import DatabaseForm
from main.admin_filters import HashFilter
from django_celery_beat.admin import PeriodicTaskAdmin
from django.utils.safestring import mark_safe
from django.contrib import admin
from django.db.models import Q
from functools import reduce
import operator
import datetime
import json


def kw(kwargs, key="database"):
    return json.loads(kwargs)[key]


@admin.register(OtherPeriodicTask)
class OtherPeriodicTaskAdmin(PeriodicTaskAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.exclude(task__in=["Dictionary", "Bruteforce"])


@admin.register(Database)
class DatabaseAdmin(admin.ModelAdmin):
    search_fields = ("id", "host", "ip", "db_type", "port", "dsn")
    readonly_fields = (
        "id",
        "is_connected",
        "last_connect_ts",
        "is_pulled",
        "last_pull_ts",
        "last_check_success",
    )
    list_display = ("id", "host", "ip", "db_type", "port", "is_disabled")
    form = DatabaseForm
    fieldsets = (
        (
            None,
            {
                "fields": ("host", "ip", "db_type", "port", "dsn"),
                "classes": ("extrapretty",),
            },
        ),
        (
            "",
            {
                "fields": (
                    "is_disabled",
                    "is_connected",
                    "last_connect_ts",
                    "is_pulled",
                    "last_pull_ts",
                    "last_check_success",
                ),
                "classes": ("extrapretty",),
            },
        ),
    )

    def port(self, obj):
        return obj.port or "default"


@admin.register(BruteConfig)
class BruteConfigAdmin(admin.ModelAdmin):
    list_display = (
        "__str__",
        "length",
        "alphabet_length",
        "combinations",
        "estimated_time_postgres",
        "estimated_time_oracle_s",
        "estimated_time_oracle_t",
        "estimated_time_mssql",
    )

    def alphabet_length(self, obj):
        if obj.custom_alphabet:
            c = len(str(self.custom_alphabet))
        else:
            c = 0
            for field in [
                "digits",
                "upper_case_en",
                "lower_case_en",
                "upper_case_ru",
                "lower_case_ru",
                "symbols",
            ]:
                if getattr(obj, field, False):
                    c += len(getattr(obj, "get_" + field, 0))
        return c

    def length(self, obj):
        if obj.min_length == obj.max_length:
            return obj.min_length
        return obj.min_length, obj.max_length

    def combinations(self, obj):
        alphabet_length = self.alphabet_length(obj)
        length = self.length(obj)
        if isinstance(length, tuple):
            len_min, len_max = length
            return alphabet_length ** len_min, alphabet_length ** len_max
        else:
            return alphabet_length ** length

    def estimated_time(self, obj, hashes_per_second):
        combs = self.combinations(obj)
        if isinstance(combs, tuple):
            comb_min, comb_max = combs
            comb_min /= hashes_per_second
            comb_max /= hashes_per_second
            try:
                return mark_safe(
                    f"{datetime.timedelta(seconds=int(comb_min))}<br>{datetime.timedelta(seconds=int(comb_max))}"
                )
            except:
                return "never"
        else:
            combs /= hashes_per_second
            return str(datetime.timedelta(seconds=int(combs)))

    # all speed values from worker1 with 4x 1070 ti
    def estimated_time_postgres(self, obj):
        speed = 10 ** 11
        return self.estimated_time(obj, speed)

    estimated_time_postgres.short_description = "ET POSTGRES (10^11 H/S)"
    estimated_time_postgres.allow_tags = True

    def estimated_time_oracle_s(self, obj):
        speed = 34 * 10 ** 9
        return self.estimated_time(obj, speed)

    estimated_time_oracle_s.short_description = "ET ORACLE S (34 * 10^9 H/S)"
    estimated_time_oracle_s.allow_tags = True

    def estimated_time_oracle_t(self, obj):
        speed = 310000
        return self.estimated_time(obj, speed)

    estimated_time_oracle_t.short_description = "ET ORACLE T (310.000 H/S)"
    estimated_time_oracle_t.allow_tags = True

    def estimated_time_mssql(self, obj):
        speed = 4 * 10 ** 9
        return self.estimated_time(obj, speed)

    estimated_time_mssql.short_description = "ET MSSQL (4 * 10^9 H/S)"
    estimated_time_mssql.allow_tags = True


@admin.register(Hash)
class HashAdmin(admin.ModelAdmin):
    search_fields = ("id", "login", "account_status")
    list_display = (
        "id",
        "is_hacked",
        "is_cracking_",
        "is_changed",
        "host",
        "login",
        "account_status",
        "hash",
        "password",
    )
    exclude = ("_encrypted_password", "_encrypted_hash", "task")
    readonly_fields = (
        "periodic_task",
        "host",
        "port",
        "db_type",
        "is_hacked",
        "account_status",
        "is_cracking",
        "login",
        "hash",
        "password",
        "created_ts",
        "cracking_started_ts",
        "hacked_ts",
    )
    list_filter = (HashFilter,)

    def get_search_results(self, request, queryset, search_term):
        if search_term:
            results = queryset.filter(
                "OR",
                hash__icontains=search_term,
                database__host__icontains=search_term,
                password__icontains=search_term,
                login__icontains=search_term,
                account_status__icontains=search_term,
            )
            return results, False
        return super().get_search_results(request, queryset, search_term)

    def host(self, obj):
        return obj.database.host

    def port(self, obj):
        return obj.database.port

    def db_type(self, obj):
        return obj.database.db_type

    def periodic_task(self, obj):
        return mark_safe(
            '<a href="/admin/main/beautifulperiodictask/{}/change/">{}</a>'.format(
                obj.task.id, obj.task
            )
        )

    def is_cracking_(self, obj):
        return (
            mark_safe('<img src="/static/admin/img/icon-yes.svg">')
            if obj.is_cracking
            else mark_safe('<img src="/static/admin/img/icon-no.svg">')
        )

    is_cracking_.short_description = "cracking"

    def is_hacked(self, obj):
        return (
            mark_safe('<img src="/static/admin/img/icon-yes.svg">')
            if obj.is_hacked
            else mark_safe('<img src="/static/admin/img/icon-no.svg">')
        )

    is_hacked.allow_tags = True
    is_hacked.short_description = "cracked"


class BasePeriodicTaskAdmin(PeriodicTaskAdmin):
    def get_search_results(self, request, queryset, search_term):
        if search_term:
            databases = Database.objects.filter(
                Q(host__icontains=search_term) | Q(db_type__icontains=search_term)
            )
            idx = [db.id for db in databases]
            if idx:
                results = queryset.filter(
                    reduce(
                        operator.or_,
                        (Q(kwargs__icontains=f'"database": {x},') for x in idx),
                    )
                )
                return results, False
        return super().get_search_results(request, queryset, search_term)

    def host(self, obj):
        return Database.objects.get(id=kw(obj.kwargs)).host

    def ip(self, obj):
        return Database.objects.get(id=kw(obj.kwargs)).ip

    def port(self, obj):
        return Database.objects.get(id=kw(obj.kwargs)).port

    def db_type(self, obj):
        return Database.objects.get(id=kw(obj.kwargs)).db_type

    def dictionary(self, obj):
        return Dictionary.objects.get(id=kw(obj.kwargs, "dictionary")).name

    def bruteforce_config(self, obj):
        return BruteConfig.objects.get(id=kw(obj.kwargs, "bruteforce_config")).name


@admin.register(DictionaryPeriodicTask)
class DictionaryPeriodicTaskAdmin(BasePeriodicTaskAdmin):
    list_display = ("__str__", "enabled", "host", "port", "ip", "db_type", "dictionary")
    form = DictionaryPeriodicTaskForm
    fieldsets = (
        (
            None,
            {
                "fields": ("name", "regtask", "enabled"),
                "classes": ("extrapretty", "wide"),
            },
        ),
        (
            "Schedule",
            {
                "fields": ("interval", "crontab"),
                "classes": (
                    "extrapretty",
                    "wide",
                ),
            },
        ),
        (
            "Keyword Arguments",
            {
                "fields": ("database", "dictionary"),
                "classes": ("extrapretty",),
            },
        ),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(task="Dictionary")


@admin.register(BruteforcePeriodicTask)
class BruteforcePeriodicTaskAdmin(BasePeriodicTaskAdmin):
    list_display = (
        "__str__",
        "enabled",
        "host",
        "port",
        "ip",
        "db_type",
        "bruteforce_config",
    )
    form = BruteforcePeriodicTaskForm
    fieldsets = (
        (
            None,
            {
                "fields": ("name", "regtask", "enabled"),
                "classes": ("extrapretty", "wide"),
            },
        ),
        (
            "Schedule",
            {
                "fields": ("interval", "crontab"),
                "classes": (
                    "extrapretty",
                    "wide",
                ),
            },
        ),
        (
            "Keyword Arguments",
            {
                "fields": ("database", "bruteforce_config"),
                "classes": ("extrapretty", "wide"),
            },
        ),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(task="Bruteforce")


def reduction_file_size(file_size):
    unit = "BKMGT"
    i = 0
    while file_size / 1024.0 > 1.0:
        file_size /= 1024.0
        i += 1
    return f"{round(file_size, 2)} {unit[i]}"


def reduction_word_count(n):
    unit = ["", "thousand", "million", "billion", "trillion"]
    i = 0
    while n / 1000.0 > 1.0:
        n /= 1000.0
        i += 1
    if i == 0:
        return None
    return f"{round(n, 2)} {unit[i]}"


@admin.register(Dictionary)
class DictionaryAdmin(admin.ModelAdmin):
    list_display = ("name", "path", "word_count_", "file_size_")

    def word_count_(self, obj):
        if obj.word_count == 0:
            return "didn`t count yet"
        return f"{obj.word_count} " + (
            f"({reduction_word_count(obj.word_count)})"
            if reduction_word_count(obj.word_count)
            else ""
        )

    def file_size_(self, obj):
        if obj.file_size == 0:
            return "didn`t count yet"
        return reduction_file_size(obj.file_size)
