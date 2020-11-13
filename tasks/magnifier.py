from main.models import Dictionary
from tasks.utils import line_count
from celery_app import app
from time import time
import logging
import os


magnifier_logger = logging.getLogger("magnifier")


@app.task(name="Magnifier")
def magnifier(**kwargs):
    try:
        # check file size
        dictionaries = Dictionary.objects.filter(file_size=0)
        for d in dictionaries:
            d.file_size = os.stat(d.path).st_size
            d.save()

        # check line count
        dictionaries = Dictionary.objects.filter(word_count=0)
        for d in dictionaries:
            st = time()
            d.word_count = line_count(d.path)
            d.save()
            magnifier_logger.info(
                f"word counted in {d.name}. Total count: {d.word_count}. Total time: {time()-st}"
            )

    except Exception as e:
        magnifier_logger.exception(e, exc_info=True)
