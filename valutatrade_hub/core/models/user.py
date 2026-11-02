import hashlib
import uuid
from datetime import datetime


class User:

    """Класс пользователя"""

    def __init__(self, user_id: int, username: str, hashed_password: str, salt: str, registration_date: datetime):

        self._user_id = user_id
        self._username = None
        self._hashed_password = hashed_password
        self._salt = salt if salt else self._generate_salt()
        self._registration_date = registration_date

        self.username = username

    @staticmethod
    def _generate_salt() -> str:
        return uuid.uuid4().hex[:8]

    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        return hashlib.sha256((password + salt).encode("utf-8")).hexdigest()

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def username(self) -> str:
        return self._username

    @property
    def hashed_password(self) -> str:
        return self._hashed_password

    @property
    def salt(self) -> str:
        return self._salt

    @property
    def registration_date(self) -> datetime:
        return self._registration_date

    @username.setter
    def username(self, value: str) -> None:
        """Сеттер username с проверкой на непустоту"""
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Имя пользователя не может быть пустым.")
        self._username = value.strip()

    @hashed_password.setter
    def hashed_password(self, value: str) -> None:
        if not isinstance(value, str):
            raise ValueError("Хеш пароля должен быть строкой.")
        self._hashed_password = value

    def get_user_info(self) -> dict:
        info = {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date
        }
        print(f"user_id: {self.user_id}")
        print(f"username: {self.username}")
        print(f"registration_date: {self.registration_date}")

        return info

    def change_password(self, new_password: str) -> None:
        self._hashed_password = self._hash_password(new_password, self._salt)

    def verify_password(self, password: str) -> bool:
        if not isinstance(password, str):
            return False
        return self._hash_password(password, self._salt) == self._hashed_password
