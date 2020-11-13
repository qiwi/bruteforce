from main.exceptions import HashNotValidException
from crypto.exceptions import HashcatException
from django.conf import settings
import subprocess
import binascii
import os
import re


# attack mods
STRAIGHT = 0  # dictionary
COMBINATIONS = 1
BRUTE_FORCE = 3
HYBRID_WORDLIST_PLUS_MASK = 6
HYBRID_MASK_PLUS_WORDLIST = 7

POSTGRES = 10  # 12 mode bugged
ORACLE_BASIC = 3100
ORACLE_H = 20
ORACLE_S = 112
ORACLE_T = 12300
MSSQL2000 = 131
MSSQL2005 = 132
MSSQL2012 = 1731  # also for 2014


def prepare_hash(db_type, hash_: str, login=None):
    if db_type == "postgres":
        if hash_.startswith("md5"):
            return POSTGRES, hash_[3:] + ":" + login
        else:
            return POSTGRES, hash_ + ":" + login
    if db_type == "oracle":
        if len(hash_) == 16:
            return ORACLE_BASIC, hash_ + ":" + login
        elif "H:" in hash_:
            parsed = re.search(r"H:([a-zA-Z0-9]+)", hash_).group(1)
            return (
                ORACLE_H,
                parsed + ":" + binascii.hexlify((login + ":XDB:").encode()).decode(),
            )
        elif "S:" in hash_:
            parsed = re.search(r"S:([a-zA-Z0-9]+)", hash_).group(1)
            return ORACLE_S, parsed[:-20] + ":" + parsed[-20:]
        elif "T:" in hash_:
            parsed = re.search(r"T:([a-zA-Z0-9]+)", hash_).group(1)
            return ORACLE_T, parsed
    if db_type == "mssql":
        if len(hash_) == 94 and hash_.startswith("0x"):
            return MSSQL2000, hash_
        elif len(hash_) == 54 and hash_.startswith("0x"):
            return MSSQL2005, hash_
        elif len(hash_) == 142 and hash_.startswith("0x"):
            return MSSQL2012, hash_
    raise HashNotValidException(f"Hash not recognized - {hash_}")


class Hashcat:
    def __init__(self, logger=None):
        self.cwd = os.path.dirname(settings.BASE_DIR)
        self.logger = logger
        self.hashcat = "/usr/local/bin/hashcat"
        self.session_name = "session"
        self.hash_type = None
        self.hashes_for_brute = []

    def _raise_if_not_implemented(self, attack_mode):
        if attack_mode not in [STRAIGHT, BRUTE_FORCE]:
            raise HashcatException(f"Attack mode -a{attack_mode} not implemented")

    def _run_process_and_wait(self, command):
        subprocess.call(command, cwd=self.cwd)

    def add_hash(self, db_type, hash_, login=None):
        hash_type, line = prepare_hash(db_type, hash_, login)
        if self.hash_type is None:
            self.hash_type = hash_type
        elif self.hash_type != hash_type:
            raise HashcatException(
                f"Hash type has been changed in one session. "
                f"Hash fragment: {hash_[7:]}. DB type: {db_type}"
            )
        self.hashes_for_brute.append(line)

    def _prepare_input_file(self, input_path):
        with open(input_path, "w", encoding="utf-8") as f:
            f.write("\n".join(self.hashes_for_brute))

    def continue_last_cracking(self):
        command = [
            self.hashcat,
            f"--restore",
            f"--restore-file-path",
            os.path.join(self.cwd, "session", f"{self.session_name}.restore"),
            f"--session",
            self.session_name,
        ]
        self._run_process_and_wait(command)

    def start_cracking(self, attack_mode, **kwargs):
        if len(self.hashes_for_brute) == 0:
            return
        self._raise_if_not_implemented(attack_mode)
        self._prepare_input_file(self.kw("input_path", **kwargs))
        command = [
            self.hashcat,
            f"-m{self.hash_type}",
            f"-a{attack_mode}",
            f"-w3",
            f"-O",
            f"--restore-file-path",
            os.path.join(self.cwd, "session", f"{self.session_name}.restore"),
            f"--potfile-disable",
            f"--session",
            self.session_name,
        ]
        if self.hash_type == ORACLE_H:
            command.append("--hex-salt")
        if attack_mode == STRAIGHT:
            command.extend(self._dict(**kwargs))
        elif attack_mode == BRUTE_FORCE:
            command.extend(self._brute_force(**kwargs))
        self._run_process_and_wait(command)

    def kw(self, key, **kwargs):
        if not kwargs.get(key):
            raise HashcatException(f"{key} not set")
        return str(kwargs.get(key))

    def _dict(self, **kwargs):
        return [
            os.path.join(self.cwd, self.kw("input_path", **kwargs)),
            self.kw("dict_path", **kwargs),
            "-o",
            os.path.join(self.cwd, self.kw("output_path", **kwargs)),
        ]

    def _brute_force(self, **kwargs):
        return [
            os.path.join(self.cwd, self.kw("input_path", **kwargs)),
            "-o",
            os.path.join(self.cwd, self.kw("output_path", **kwargs)),
            "-i",
            "--increment-min",
            self.kw("min_length", **kwargs),
            "--increment-max",
            self.kw("max_length", **kwargs),
            "-1",
            f'"{self.kw("alphabet", **kwargs)}"',
            "?1" * int(self.kw("max_length", **kwargs)),
        ]
