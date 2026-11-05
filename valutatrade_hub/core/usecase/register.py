import uuid
from datetime import datetime

from valutatrade_hub.core.models.user import User
from valutatrade_hub.core.utils.exceptions import RegisterError
from valutatrade_hub.infra.database import db


def register(username: str, password: str) -> User:
    if not username or not username.strip():
        raise RegisterError("Имя пользователя не может быть пустым")
    if not password or len(password) < 4:
        raise RegisterError("Пароль должен быть не короче 4 символов")

    users = db.load_users()
    if any(u["username"].lower() == username.lower() for u in users):
        raise RegisterError(f"Имя пользователя '{username}' уже занято")

    user_id = max((u["user_id"] for u in users), default=0) + 1
    salt = uuid.uuid4().hex[:8]
    hashed = User._hash_password(password, salt)
    reg_date = datetime.now()

    record = {
        "user_id": user_id,
        "username": username,
        "hashed_password": hashed,
        "salt": salt,
        "registration_date": reg_date.isoformat(timespec="seconds"),
    }
    users.append(record)
    db.save_users(users)

    portfolios = db.load_portfolios()
    portfolios.append({"user_id": user_id, "wallets": {"USD": {"balance": 10000.0}}})
    db.save_portfolios(portfolios)

    return User(user_id, username, hashed, salt, reg_date)