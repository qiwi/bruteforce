from crypto.utils import AESCipher
from django.conf import settings


aes = AESCipher(settings.CRYPTO_KEY)


class EncryptedHashMixin(object):
    @property
    def hash(self):
        if not self._encrypted_hash:
            return None
        return aes.decrypt(self._encrypted_hash.encode())

    @hash.setter
    def hash(self, value):
        self._encrypted_hash = aes.encrypt(value).decode() if value else None


class EncryptedPasswordMixin(object):
    @property
    def password(self):
        if not self._encrypted_password:
            return None
        return aes.decrypt(self._encrypted_password.encode())

    @password.setter
    def password(self, value):
        self._encrypted_password = aes.encrypt(value).decode() if value else None

    @property
    def is_hacked(self):
        return bool(self._encrypted_password)


class AlphabetMixin(object):
    @property
    def get_digits(self):
        return "0123456789"

    @property
    def get_upper_case_en(self):
        return "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    @property
    def get_lower_case_en(self):
        return "abcdefghijklmnopqrstuvwxyz"

    @property
    def get_upper_case_ru(self):
        return "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"

    @property
    def get_lower_case_ru(self):
        return "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"

    @property
    def get_symbols(self):
        return "!\"#$%&'()*+,-./:;<=>?@[\]^_`{|}~ "

    @property
    def get_alphabet(self):
        if self.custom_alphabet:
            return self.custom_alphabet
        return "".join(
            [
                getattr(self, f"get_{field}")
                for field in [
                    "digits",
                    "upper_case_en",
                    "lower_case_en",
                    "upper_case_ru",
                    "lower_case_ru",
                    "symbols",
                ]
                if getattr(self, field, False)
            ]
        )
