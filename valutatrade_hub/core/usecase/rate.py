from datetime import UTC, datetime, timedelta

from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.core.utils.exceptions import (
    ApiRequestError,
    CurrencyNotFoundError,
    RateError,
)
from valutatrade_hub.infra.database import db
from valutatrade_hub.infra.settings import SettingsLoader

STUB_RATES_TO_USD: dict[str, float] = {
    "USD": 1.0, "EUR": 1.0786, "GBP": 1.27,
    "BTC": 59337.21, "ETH": 3720.00, "RUB": 0.01016,
}


def _now() -> datetime:
    return datetime.now()


def _now_iso() -> str:
    return _now().isoformat(timespec="seconds")


def _ttl() -> timedelta:
    seconds = SettingsLoader().get("RATES_TTL_SECONDS", 300)
    return timedelta(seconds=int(seconds))


def _is_fresh(updated_at: str) -> bool:
    if not updated_at:
        return False
    try:
        dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        now = datetime.now(UTC)
        return now - dt <= _ttl()
    except (ValueError, TypeError):
        return False


def _fetch_from_parser(from_code: str, to_code: str) -> float | None:
    if from_code not in STUB_RATES_TO_USD or to_code not in STUB_RATES_TO_USD:
        raise ApiRequestError(f"нет данных для {from_code}->{to_code}")
    return STUB_RATES_TO_USD[from_code] / STUB_RATES_TO_USD[to_code]

# cache
def _make_cache(ttl: timedelta):
    cache: dict[tuple, tuple[float, datetime]] = {}

    def get_cached(func, *args):
        now = _now()
        if args in cache:
            result, ts = cache[args]
            if now - ts < ttl:
                return result, ts.isoformat(timespec="seconds")
        result = func(*args)
        if result is not None:
            cache[args] = (result, now)
        return result, now.isoformat(timespec="seconds")

    return get_cached


_get_cached = _make_cache(_ttl())


def _load_from_file_or_parser(from_code: str, to_code: str) -> float | None:
    cache_data = db.load_rates()
    key, rev = f"{from_code}_{to_code}", f"{to_code}_{from_code}"

    if key in cache_data and _is_fresh(cache_data[key].get("updated_at", "")):
        return float(cache_data[key]["rate"])

    if rev in cache_data and _is_fresh(cache_data[rev].get("updated_at", "")):
        r = float(cache_data[rev]["rate"])
        if r > 0:
            return 1.0 / r

    rate = _fetch_from_parser(from_code, to_code)
    if rate is None:
        return None

    ts = _now_iso()
    cache_data[key] = {"rate": rate, "updated_at": ts}
    if rate > 0:
        cache_data[rev] = {"rate": 1.0 / rate, "updated_at": ts}
    cache_data["source"] = "ParserService"
    cache_data["last_refresh"] = ts
    db.save_rates(cache_data)
    return rate


def get_rate(from_code: str, to_code: str) -> tuple[float | None, str | None]:
    from_c = (from_code or "").strip().upper()
    to_c = (to_code or "").strip().upper()
    if not from_c or not to_c:
        return None, None
    if from_c == to_c:
        return 1.0, _now_iso()
    return _get_cached(_load_from_file_or_parser, from_c, to_c)




def get_rate_info(from_code: str, to_code: str) -> dict:
    try:
        src = get_currency(from_code)
        dst = get_currency(to_code)
    except CurrencyNotFoundError as e:
        raise RateError(str(e))

    if src.code == dst.code:
        return {"from": src.code, "to": dst.code, "rate": 1.0,
                "updated_at": None, "reverse_rate": 1.0}

    try:
        rate, updated_at = get_rate(src.code, dst.code)
    except ApiRequestError as e:
        raise RateError(str(e))

    if rate is None:
        raise RateError(
            f"Курс {src.code}→{dst.code} недоступен.")

    reverse, _ = get_rate(dst.code, src.code)
    return {"from": src.code, "to": dst.code, "rate": rate,
            "updated_at": updated_at, "reverse_rate": reverse}