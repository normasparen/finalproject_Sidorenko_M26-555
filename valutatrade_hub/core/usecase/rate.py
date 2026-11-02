
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

from valutatrade_hub.core import storage
from valutatrade_hub.core.storage import get_cached, load_rate_from_storage_or_parser
from valutatrade_hub.core.utils.exceptions import RateError
from valutatrade_hub.core.utils.utility import now_iso


def get_rate(from_code: str, to_code: str) -> Tuple[Optional[float], Optional[str]]:
    """
    Сначала смотрим в замыкание (кеш), потом в json, потом в парсер.
    """
    from_code = from_code.strip().upper()
    to_code = to_code.strip().upper()

    if not from_code or not to_code:
        return None, None
    if from_code == to_code:
        return 1.0, now_iso()

    rate, updated_at = get_cached(load_rate_from_storage_or_parser, from_code, to_code)
    return rate, updated_at



def get_rate_info(from_code: str, to_code: str) -> dict:
    """
    Возвращает информацию о курсе одной валюты к другой.
    """
    if not from_code or not from_code.strip() or not to_code or not to_code.strip():
        raise RateError("Коды валют не могут быть пустыми")

    from_c = from_code.strip().upper()
    to_c = to_code.strip().upper()

    if from_c == to_c:
        return {
            "from": from_c,
            "to": to_c,
            "rate": 1.0,
            "updated_at": None,
            "reverse_rate": 1.0,
        }

    rate, updated_at = get_rate(from_c, to_c)
    if rate is None:
        raise RateError(f"Курс {from_c}→{to_c} недоступен. Повторите попытку позже.")

    reverse_rate, _ = get_rate(to_c, from_c)

    return {
        "from": from_c,
        "to": to_c,
        "rate": rate,
        "updated_at": updated_at,
        "reverse_rate": reverse_rate,
    }