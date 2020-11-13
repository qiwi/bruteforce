from tasks.utils import get_user_data
from main.models import Hash
from celery_app import app
import logging


change_checker_logger = logging.getLogger("change_checker")


@app.task(name="Change checker")
def change_checker():
    try:
        hacked_hashes = Hash.objects.filter(is_hacked=True)
        databases = list(set(h.database for h in hacked_hashes))
        for db in databases:
            data = get_user_data(db.host, db.db_type, dsn=db.dsn)
            for h in hacked_hashes.filter(database=db):
                found = False
                for row in data:
                    if row[0] == h.login:
                        found = True
                        h.is_changed = h.hash.lower() not in row[1].lower()
                        h.account_status = row[2]
                        h.save()
                        break
                if not found:
                    h.is_changed = True
                    h.account_status = "DELETED"
                    h.save()
    except Exception as e:
        change_checker_logger.exception(e, exc_info=True)
