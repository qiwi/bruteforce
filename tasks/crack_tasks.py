from tasks.base_task import base_cracking_task
from crypto.hashcat import STRAIGHT, BRUTE_FORCE

from celery_app import app
import logging

task_logger = logging.getLogger("brute_tasks")


@app.task(name="Bruteforce")
def brute_force(**kwargs: dict):
    base_cracking_task(crack_type=BRUTE_FORCE, **kwargs)


@app.task(name="Dictionary")
def brute_force_dict(**kwargs: dict):
    base_cracking_task(crack_type=STRAIGHT, **kwargs)
