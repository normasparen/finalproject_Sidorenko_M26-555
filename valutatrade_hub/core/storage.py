import json
import os
from datetime import timedelta, datetime
from typing import Any, Dict, List, Tuple, Optional

from valutatrade_hub.core.utils.utility import is_fresh, fetch_from_parser, now_iso

DATA_DIR = "data"

USERS_FILE = os.path.join(DATA_DIR, "users.json")
PORTFOLIOS_FILE = os.path.join(DATA_DIR, "portfolios.json")
RATES_FILE = os.path.join(DATA_DIR, "rates.json")
CACHE_TTL = timedelta(minutes=5)



def _ensure_data_dir() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)


def load_json(path: str, default: Any) -> Any:
    """Загружает json"""
    _ensure_data_dir()
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
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
    cache: Dict[tuple, Tuple[any, datetime]] = {}

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


def load_rate_from_storage_or_parser(from_code: str, to_code: str) -> Optional[float]:
    """Смотрит в rates.json. Если свежие данные, то берем их. Иначе - апи + сохранение."""
    key = f"{from_code}_{to_code}"
    reverse_key = f"{to_code}_{from_code}"

    # читаем файл
    cache_data = load_rates()

    if key in cache_data and is_fresh(cache_data[key].get("updated_at", "")):
        return float(cache_data[key]["rate"])

    if reverse_key in cache_data and is_fresh(cache_data[reverse_key].get("updated_at", "")):
        rev = float(cache_data[reverse_key]["rate"])
        if rev > 0:
            return 1.0 / rev

    #  если файл устарел то идем в парсер
    rate = fetch_from_parser(from_code, to_code)
    if rate is None:
        return None

    #  сохраняем в файл
    updated_at = now_iso()
    cache_data[key] = {"rate": rate, "updated_at": updated_at}
    if rate > 0:
        cache_data[reverse_key] = {"rate": 1.0 / rate, "updated_at": updated_at}
    cache_data["source"] = "ParserService"
    cache_data["last_refresh"] = updated_at
    save_rates(cache_data)

    return rate


# Пользовател
def load_users() -> List[Dict]:
    return load_json(USERS_FILE, [])


def save_users(users: List[Dict]) -> None:
    save_json(USERS_FILE, users)


def load_portfolios() -> List[Dict]:
    return load_json(PORTFOLIOS_FILE, [])


def save_portfolios(portfolios: List[Dict]) -> None:
    save_json(PORTFOLIOS_FILE, portfolios)


def load_rates() -> Dict:
    return load_json(RATES_FILE, {})


def save_rates(rates: Dict) -> None:
    save_json(RATES_FILE, rates)