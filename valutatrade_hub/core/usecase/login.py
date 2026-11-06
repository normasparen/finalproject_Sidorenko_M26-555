from valutatrade_hub.core.models.user import User
from valutatrade_hub.core.session import Session
from valutatrade_hub.core.utils.exceptions import LoginError
from valutatrade_hub.infra.database import db


def login(username: str, password: str) -> User:
    users = db.load_users()
    record = next(
        (u for u in users if u["username"].lower() == username.lower()), None
    )
    if record is None:
        raise LoginError(f"Пользователь '{username}' не найден")

    salt = record.get("salt", "")
    if User._hash_password(password, salt) != record["hashed_password"]:
        raise LoginError("Неверный пароль")

    user = User.from_dict(record)
    Session.login(user)
    return user