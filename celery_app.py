from __future__ import absolute_import, unicode_literals

import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bruteforce.settings.prod")

app = Celery("bruteforce")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.conf.task_default_queue = "bruteforce"
app.conf.task_default_exchange = "bruteforce"
app.conf.task_default_routing_key = "bruteforce"
app.autodiscover_tasks()
