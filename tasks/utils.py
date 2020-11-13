from db.connectors import OracleConnector, PgConnector, MssqlConnector
from itertools import takewhile, repeat
from datetime import datetime, timezone
from db.connectors import get_user_data
from main.models import Hash, Database
from django.conf import settings
from crypto import AESCipher
import typing
import os


aes = AESCipher(key=settings.CRYPTO_KEY)
CONNECTORS: typing.Dict[str, typing.Any] = {
    "postgres": PgConnector,
    "oracle": OracleConnector,
    "mssql": MssqlConnector,
}


def get_files(walk_path, prefix="output"):
    out_files = []
    for path, _, files in list(os.walk(walk_path)):
        for file in files:
            if file.startswith(prefix):
                out_files.append((path, file))
    return out_files


def line_count(filename):
    f = open(filename, "rb")
    f_read = f.raw.read
    step = 1024 * 1024 * 10
    bufgen = takewhile(lambda x: x, (f_read(step) for _ in repeat(None)))
    return sum(buf.count(b"\n") for buf in bufgen)


def commit_results(data=None):
    if data is None:
        data = {}
    files = get_files("temp")
    cracked_count = 0
    for path, file in files:
        _, host, db_type, _ = file.split("__")
        with open(os.path.join(path, file), encoding="utf-8") as f:
            results = {
                line.split(":")[0]: line.split(":")[-1]
                for line in f.read().split("\n")
                if line
            }
            cracked_count = len(results)
            if host not in data and cracked_count != 0:
                db = Database.objects.get(host=host)
                data[host] = get_user_data(
                    host=host, db_type=db_type, port=db.port, dsn=db.dsn
                )
            for login, source_hash, _ in data.get(host, []):
                password = [
                    password
                    for hash_fragment, password in results.items()
                    if hash_fragment.lower() in source_hash.lower()
                ]
                hashes = Hash.objects.filter(hash__icontains=source_hash)
                if password:
                    hashes.update(
                        _encrypted_password=aes.encrypt(password[0]).decode("utf-8"),
                        hacked_ts=datetime.now(tz=timezone.utc),
                        is_cracking=False,
                    )
                else:
                    hashes.update(
                        is_cracking=False,
                    )
        os.remove(os.path.join(path, file))
        try:
            os.remove(os.path.join(path, file.replace("output", "input")))
        except:
            pass
    return cracked_count
