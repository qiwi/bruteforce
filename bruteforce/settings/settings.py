import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEBUG = False

ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "main",
    "tasks",
    "django_celery_beat",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "bruteforce.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(os.path.dirname(BASE_DIR), "templates")],
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
            "loaders": [
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
        },
    },
]

WSGI_APPLICATION = "bruteforce.wsgi.application"


# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(os.path.dirname(BASE_DIR), "static")

LOG_DIR = "/var/log/bruteforce/"
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
    "formatters": {
        "basic": {
            "format": "%(asctime)s | %(levelname)s | %(filename)s | %(funcName)s [line %(lineno)d]: %(message)s"
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": os.path.join(LOG_DIR, "console.log"),
            "formatter": "basic",
        },
        "sync": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": os.path.join(LOG_DIR, "sync.log"),
            "formatter": "basic",
        },
        "connectors": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": os.path.join(LOG_DIR, "connectors.log"),
            "formatter": "basic",
        },
        "brute_tasks": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": os.path.join(LOG_DIR, "brute_tasks.log"),
            "formatter": "basic",
        },
        "magnifier": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": os.path.join(LOG_DIR, "magnifier.log"),
            "formatter": "basic",
        },
        "change_checker": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": os.path.join(LOG_DIR, "change_checker.log"),
            "formatter": "basic",
        },
        "errors": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filters": ["require_debug_false"],
            "filename": os.path.join(LOG_DIR, "errors.log"),
            "formatter": "basic",
        },
    },
    "loggers": {
        "console": {"level": "DEBUG", "handlers": ["console"]},
        "errors": {"level": "DEBUG", "handlers": ["errors"]},
        "sync": {"level": "INFO", "handlers": ["sync"]},
        "connectors": {"level": "INFO", "handlers": ["connectors"]},
        "brute_tasks": {"level": "INFO", "handlers": ["brute_tasks"]},
        "magnifier": {"level": "INFO", "handlers": ["magnifier"]},
        "change_checker": {"level": "INFO", "handlers": ["change_checker"]},
    },
}
