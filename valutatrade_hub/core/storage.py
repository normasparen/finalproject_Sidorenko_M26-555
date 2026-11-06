import json
import os
from datetime import UTC, datetime, timedelta
from typing import Any

DATA_DIR = "data"

USERS_FILE = os.path.join(DATA_DIR, "users.json")
PORTFOLIOS_FILE = os.path.join(DATA_DIR, "portfolios.json")
RATES_FILE = os.path.join(DATA_DIR, "rates.json")
CACHE_TTL = timedelta(minutes=5)






def is_fresh(updated_at: str, ttl: timedelta = CACHE_TTL) -> bool:
    if not updated_at:
        return False
    try:
        dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return datetime.now(UTC) - dt <= ttl
    except (ValueError, TypeError):
        return False

def _ensure_data_dir() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)


def load_json(path: str, default: Any) -> Any:
    """Загружает json"""
    _ensure_data_dir()
    if not os.path.exists(path):
        return default
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read().strip()
            return json.loads(content) if content else default
    except (json.JSONDecodeError, OSError):
        return default


def save_json(path: str, data: Any) -> None:
    """Сохраняет данные в json"""
    _ensure_data_dir()
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def make_rate_cache(ttl: timedelta = CACHE_TTL):
    """
    Создает замыкание для кэша
    """
    cache: dict[tuple, tuple[any, datetime]] = {}

    def get_cached(func, *args):
        now = datetime.now()
        if args in cache:
            result, timestamp = cache[args]
            if now - timestamp < ttl:
                # если данные свежие, то берем из памяти
                return result, timestamp.isoformat(timespec="seconds")

        # вызываем функцию (которая сходит в файл или апи)
        result = func(*args)
        if result is not None:
            cache[args] = (result, now)
        return result, now.isoformat(timespec="seconds") if result is not None else None

    return get_cached


# глобальный кэш (один на все вызовы в сессии)
get_cached = make_rate_cache()

def load_rate_from_storage_or_parser(from_code: str, to_code: str) -> float | None:
    """
    Только читает rates.json. Если данных нет или они устарели - возвращает None.
    """
    key = f"{from_code}_{to_code}"
    reverse_key = f"{to_code}_{from_code}"

    cache_data = load_rates()

    if key in cache_data and is_fresh(cache_data[key].get("updated_at", "")):
        return float(cache_data[key]["rate"])

    if reverse_key in cache_data and is_fresh(cache_data[reverse_key].get("updated_at", "")):
        rev = float(cache_data[reverse_key]["rate"])
        if rev > 0:
            return 1.0 / rev

    # Ничего не пишем возвращаем None
    return None


# Пользовател
def load_users() -> list[dict]:
    return load_json(USERS_FILE, [])


def save_users(users: list[dict]) -> None:
    save_json(USERS_FILE, users)


def load_portfolios() -> list[dict]:
    return load_json(PORTFOLIOS_FILE, [])


def save_portfolios(portfolios: list[dict]) -> None:
    save_json(PORTFOLIOS_FILE, portfolios)


def load_rates() -> dict:
    return load_json(RATES_FILE, {})


def save_rates(rates: dict) -> None:
    save_json(RATES_FILE, rates)