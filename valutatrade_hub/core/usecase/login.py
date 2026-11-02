from datetime import datetime

from valutatrade_hub.core.models import User
from valutatrade_hub.core.session import Session
from valutatrade_hub.core.usecase.portfolio import load_portfolio_for_user
from valutatrade_hub.core.utils.exceptions import LoginError
from valutatrade_hub.core.utils.utility import find_user, hash_password


def login(username: str, password: str) -> User:
    record = find_user(username)
    if record is None:
        raise LoginError(f"Пользователь '{username}' не найден")

    salt = record.get("salt", "")
    expected = record["hashed_password"]
    if hash_password(password, salt) != expected:
        raise LoginError("Неверный пароль")

    user = User(
        user_id=record["user_id"],
        username=record["username"],
        hashed_password=record["hashed_password"],
        salt=salt,
        registration_date=datetime.fromisoformat(record["registration_date"]),
    )

    Session.current_user = user
    Session.current_portfolio = load_portfolio_for_user(user.user_id)
    return user
