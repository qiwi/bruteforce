from crypto.hashcat import Hashcat, STRAIGHT, BRUTE_FORCE, prepare_hash
from main.models import Dictionary, BruteConfig, Hash, Database
from datetime import datetime, timezone
from db.connectors import get_user_data
from tasks.utils import commit_results
import logging
import typing
import string
import re

task_logger = logging.getLogger("brute_tasks")

subfolder: typing.Dict[int, str] = {STRAIGHT: "dictionary", BRUTE_FORCE: "bruteforce"}
INPUT_PATH = "temp/{}/input_hashes__{}__{}__.txt"
OUTPUT_PATH = "temp/{}/output_hashes__{}__{}__.txt"

fields: typing.Dict[int, str] = {STRAIGHT: "dictionary", BRUTE_FORCE: "brute_config"}


ORACLE_SYS_HASHES = [
    "GLOBAL",
    "OUTLN",
    "EXTERNAL",
    "ORACLE_OCM",
    "OLAPSYS",
    "TSMSYS",
    "WKPROXY",
    "MDDATA",
    "anonymous",
    "XDB",
    "CTXSYS",
    "MDSYS",
    "ORDPLUGINS",
    "ORDSYS",
    "EXFSYS",
    "WMSYS",
    "DBSNMP",
    "DMSYS",
    "DIP",
    "SI_INFORMTN_SCHEMA",
    "XS$NULL",
    "WK_TEST",
]


def normalize_oracle_hashes(data):
    hexdigits = set(string.hexdigits)
    filtered_data = [row for row in data if row[1] not in ORACLE_SYS_HASHES]
    if all(
        len(row[1]) == 16 and set(row[1]).issubset(hexdigits) for row in filtered_data
    ):
        normalized_data = filtered_data
    elif all("H:" in row[1] for row in filtered_data):
        normalized_data = [
            (row[0], re.search(r"H:[a-zA-Z0-9]+", row[1]).group(0), row[2])
            for row in filtered_data
        ]
    elif all("S:" in row[1] for row in filtered_data):
        normalized_data = [
            (row[0], re.search(r"S:[a-zA-Z0-9]+", row[1]).group(0), row[2])
            for row in filtered_data
        ]
    elif all("T:" in row[1] for row in filtered_data):
        normalized_data = [
            (row[0], re.search(r"T:[a-zA-Z0-9]+", row[1]).group(0), row[2])
            for row in filtered_data
        ]
    else:
        raise Exception("Hashes were not normalized")
    return normalized_data


def base_cracking_task(crack_type: int, **kwargs: typing.Dict[typing.Any, typing.Any]):
    try:
        db = Database.objects.get(id=int(kwargs.get("database", '')))
        task_logger.info(f"run task: {crack_type} {db.host}")
        if db.is_disabled:
            task_logger.info(f'task: {kwargs.get("name")} was disabled')
            return
        hashcat = Hashcat()
        hashcat.continue_last_cracking()
        commit_results()

        db_type = db.db_type
        host = db.host
        dsn = db.dsn

        config: typing.Any = None
        if crack_type == STRAIGHT:
            config = Dictionary.objects.get(id=int(kwargs.get("dictionary", '')))
        elif crack_type == BRUTE_FORCE:
            config = BruteConfig.objects.get(id=int(kwargs.get("bruteforce_config", '')))
        else:
            raise Exception("Crack type not implemented")
        input_path = INPUT_PATH.format(subfolder.get(crack_type), host, db_type)
        output_path = OUTPUT_PATH.format(subfolder.get(crack_type), host, db_type)
        with open(output_path, "w", encoding="utf-8"):
            pass

        data = get_user_data(host=host, db_type=db_type, dsn=dsn)

        # if db_type == "oracle":
        #     data = normalize_oracle_hashes(data)

        prepared_hashes: typing.Dict[int, typing.List] = {}

        for login, hash_, account_status in data:
            account_status = str(account_status)
            const_params = dict(
                login=login,
                database=db,
                account_status=account_status,
            )
            added_hashes = Hash.objects.filter(
                database=db,
                login=login,
            )
            # 1-2
            if not added_hashes.exists():
                same_hashes = Hash.objects.filter(login=login, hash=hash_)
                # 1.6
                if not same_hashes.exists():
                    new_hash = Hash.objects.create(
                        cracking_started_ts=datetime.now(tz=timezone.utc),
                        is_cracking=True,
                        **const_params,
                    )
                    getattr(new_hash, fields.get(crack_type, '')).add(config)
                    new_hash.hash = hash_
                    new_hash.save()
                    # hashcat.add_hash(db_type, hash_, login)
                    hash_type, raw_hash = prepare_hash(db_type, hash_, login)
                    if hash_type not in prepared_hashes:
                        prepared_hashes.update({hash_type: []})
                    prepared_hashes[hash_type].append((hash_, login))
                # 2
                else:
                    cracked_hashes = same_hashes.filter(is_hacked=True)
                    # 2.1
                    if cracked_hashes.exists():
                        new_hash = Hash.objects.create(
                            is_cracking=False,
                            hacked_ts=datetime.now(tz=timezone.utc),
                            **const_params,
                        )
                        cracked_hash = cracked_hashes.first()
                        new_hash.password = cracked_hash.password
                        getattr(new_hash, fields[crack_type]).add(config)
                        new_hash.hash = hash_
                        new_hash.save()
                    # 2.2-2.5
                    else:
                        same_config_hashes = same_hashes.filter(
                            **{f"{fields[crack_type]}__id": config.id}
                        )
                        exists = same_config_hashes.exists()
                        new_hash = Hash.objects.create(
                            cracking_started_ts=datetime.now(tz=timezone.utc)
                            if not exists
                            else None,
                            is_cracking=not exists,
                            **const_params,
                        )
                        getattr(new_hash, fields[crack_type]).add(config)
                        new_hash.hash = hash_
                        new_hash.save()
                        if not exists:
                            # hashcat.add_hash(db_type, hash_, login)
                            hash_type, raw_hash = prepare_hash(db_type, hash_, login)
                            if hash_type not in prepared_hashes:
                                prepared_hashes.update({hash_type: []})
                            prepared_hashes[hash_type].append((hash_, login))
            else:  # 3-4
                hash_equals = added_hashes.filter(hash=hash_)

                if not hash_equals.exists():
                    # added_hashes.update(is_changed=True)
                    new_hash = Hash.objects.create(
                        cracking_started_ts=datetime.now(tz=timezone.utc),
                        is_cracking=True,
                        **const_params,
                    )
                    getattr(new_hash, fields[crack_type]).add(config)
                    new_hash.hash = hash_
                    new_hash.save()
                    # hashcat.add_hash(db_type, hash_, login)
                    hash_type, raw_hash = prepare_hash(db_type, hash_, login)
                    if hash_type not in prepared_hashes:
                        prepared_hashes.update({hash_type: []})
                    prepared_hashes[hash_type].append((hash_, login))
                else:  # 4.3 4.5
                    # 4.1
                    hash_equals = hash_equals.filter(_encrypted_password__isnull=True)
                    if not hash_equals.exists():
                        continue
                    # added_hashes.exclude(hash=hash_).update(is_changed=True)
                    h = hash_equals[0]  # always 1 record, if it >1 then something wrong
                    h.is_changed = False
                    h.save()
                    if not hash_equals.filter(
                        **{f"{fields[crack_type]}__id": config.id}
                    ).exists():
                        getattr(h, fields[crack_type]).add(config)
                        # hashcat.add_hash(db_type, hash_, login)
                        hash_type, raw_hash = prepare_hash(db_type, hash_, login)
                        if hash_type not in prepared_hashes:
                            prepared_hashes.update({hash_type: []})
                        prepared_hashes[hash_type].append((hash_, login))
                    h.save()
        if crack_type == STRAIGHT:
            kw = {"dict_path": config.path}
        elif crack_type == BRUTE_FORCE:
            kw = {
                "alphabet": config.get_alphabet,
                "min_length": config.min_length,
                "max_length": config.max_length,
            }
        else:
            kw = {}
        cracked_count = 0
        hash_count = len(sum(prepared_hashes.values(), [])) if prepared_hashes else 0
        for hash_type, hash_list in prepared_hashes.items():
            hashcat = Hashcat()
            for hash_, login in hash_list:
                hashcat.add_hash(db_type, hash_, login)
            hashcat.start_cracking(
                crack_type, input_path=input_path, output_path=output_path, **kw
            )
            cracked_count += commit_results(data={host: data})
        task_logger.info(f"cracking complete, found {cracked_count}/{hash_count}")
        db.last_check_success = True
        db.save()
    except Exception as e:
        db = Database.objects.get(id=int(kwargs.get("database", '')))
        db.last_check_success = False
        db.save()
        task_logger.exception(e, exc_info=True)
