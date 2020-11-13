from bruteforce.settings.settings import *

DEBUG = False

ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "bruteforce",
        "USER": "",
        "PASSWORD": "",
        "HOST": "",
        "PORT": "5432",
    }
}

SECRET_KEY = "secret =0_0="  # django secret key

# For remote rabbitmq
# RMQ = {
#     'USERNAME': '',
#     'PASSWORD': '',
#     'VHOST': '',
#     'HOST': ''
# }
# CELERY_BROKER_URL = 'amqp://{}:{}@{}:5672/{}'.format(RMQ['USERNAME'], RMQ['PASSWORD'], RMQ['HOST'], RMQ['VHOST'])
CELERY_BROKER_URL = "amqp://localhost:5672"

CRYPTO_KEY = "another secret =0_0="  # key for db encryption

CONN_CREDENTIALS = {  # default credentials for databases
    "POSTGRES": {
        "USERNAME": "",
        "PASSWORD": "",
    },
    "ORACLE": {
        "USERNAME": "",
        "PASSWORD": "",
    },
    "MSSQL": {
        "USERNAME": "",
        "PASSWORD": "",
    },
}

CUSTOM_CREDENTIALS = {  # credentials for non-default database accounts
    "oracle.example.ru": {"USERNAME": "", "PASSWORD": "", "DSN": ""},
    "postgres.example.ru:": {"USERNAME": "test_user", "PASSWORD": "test_pwd"},
}
