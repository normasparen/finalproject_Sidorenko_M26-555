import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from valutatrade_hub.core import storage


STUB_RATES_TO_USD: Dict[str, float] = {
    "USD": 1.0,
    "EUR": 1.08,
    "GBP": 1.27,
    "BTC": 78000.0,
    "ETH": 3200.0,
    "RUB": 0.011,
}

CACHE_TTL = timedelta(minutes=5)

def fetch_from_parser(from_code: str, to_code: str) -> Optional[float]:
    """
    Тут будет вызов АПИ
    """
    if from_code not in STUB_RATES_TO_USD or to_code not in STUB_RATES_TO_USD:
        return None
    # Приводим через USD
    return STUB_RATES_TO_USD[from_code] / STUB_RATES_TO_USD[to_code]



def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def is_fresh(updated_at: str, ttl: timedelta = CACHE_TTL) -> bool:
    try:
        dt = datetime.fromisoformat(updated_at)
    except (ValueError, TypeError):
        return False
    return datetime.now() - dt <= ttl


def hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((password + salt).encode("utf-8")).hexdigest()


def next_user_id(users: List[Dict]) -> int:
    return max((u["user_id"] for u in users), default=0) + 1


def find_user(username: str) -> Optional[Dict]:
    users = storage.load_users()
    for u in users:
        if u["username"].lower() == username.lower():
            return u
    return None





