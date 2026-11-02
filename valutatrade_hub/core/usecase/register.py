import uuid
from datetime import datetime

from valutatrade_hub.core import storage
from valutatrade_hub.core.models import User
from valutatrade_hub.core.utils.exceptions import RegisterError
from valutatrade_hub.core.utils.utility import next_user_id, hash_password


def register(username: str, password: str) -> User:
    if not username or not username.strip():
        raise RegisterError("Имя пользователя не может быть пустым")
    if not password or len(password) < 4:
        raise RegisterError("Пароль должен быть не короче 4 символов")

    users = storage.load_users()
    if any(u["username"].lower() == username.lower() for u in users):
        raise RegisterError(f"Имя пользователя '{username}' уже занято")

    user_id = next_user_id(users)
    salt = uuid.uuid4().hex[:8]
    hashed = hash_password(password, salt)
    reg_date = datetime.now().isoformat(timespec="seconds")

    users.append({
        "user_id": user_id,
        "username": username,
        "hashed_password": hashed,
        "salt": salt,
        "registration_date": reg_date,
    })
    storage.save_users(users)

    # Создаём пустой портфель
    portfolios = storage.load_portfolios()
    portfolios.append({"user_id": user_id, "wallets": {}})
    storage.save_portfolios(portfolios)

    return User(
        user_id=user_id,
        username=username,
        hashed_password=hashed,
        salt=salt,
        registration_date=datetime.fromisoformat(reg_date),
    )