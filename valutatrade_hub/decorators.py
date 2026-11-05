import functools
from datetime import datetime
from typing import Any, Callable

from valutatrade_hub.logging_config import logger


def _extract_arg(args, kwargs, *names):
    """Достаёт значение из kwargs по имени или из args по позиции."""
    for name in names:
        if name in kwargs:
            return kwargs[name]
    # Если не нашли в kwargs — пробуем вытащить из args по порядку
    # (простая эвристика: username/currency/amount идут первыми)
    for val in args:
        if isinstance(val, str) and val.isupper() and 2 <= len(val) <= 5:
            return val  # похоже на код валюты
    return None


def log_action(action: str, verbose: bool = False) -> Callable:
    """
    Логирует доменную операцию (BUY/SELL/REGISTER/LOGIN) в формате:
    INFO 2025-10-09T12:05:22 BUY user='alice' currency='BTC' amount=0.0500
         rate=59300.00 base='USD' result=OK

    Исключения не глотает — пробрасывает дальше, но фиксирует их в лог.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # --- Пытаемся вытащить контекст ---
            username = (
                kwargs.get("username")
                or kwargs.get("user")
                or next((a for a in args if isinstance(a, str) and not a.isupper()), None)
            )
            currency = (
                kwargs.get("currency")
                or kwargs.get("currency_code")
                or next((a for a in args if isinstance(a, str) and a.isupper() and 2 <= len(a) <= 5), None)
            )
            amount = kwargs.get("amount")
            if amount is None:
                amount = next((a for a in args if isinstance(a, (int, float)) and not isinstance(a, bool)), None)

            rate = kwargs.get("rate", "-")
            base = kwargs.get("base", "USD")

            try:
                result = func(*args, **kwargs)

                # Обогащаем контекст из результата, если он вернул dict
                if isinstance(result, dict):
                    username = username or result.get("username")
                    currency = result.get("currency", currency)
                    amount = result.get("amount", amount)
                    rate = result.get("rate", rate)
                    base = result.get("base", base)

                # Форматируем поля
                user_str = f"'{username}'" if username else "'unknown'"
                curr_str = f"'{currency}'" if currency else "'-'"
                amount_str = f"{amount:.4f}" if isinstance(amount, (int, float)) else "-"
                rate_str = f"{rate:.2f}" if isinstance(rate, (int, float)) else str(rate)
                base_str = f"'{base}'" if base else "'-'"

                msg = (
                    f"{action} user={user_str} currency={curr_str} "
                    f"amount={amount_str} rate={rate_str} base={base_str} result=OK"
                )
                if verbose and isinstance(result, dict):
                    # Показываем изменение баланса «было → стало»
                    old = result.get("old_balance")
                    new = result.get("new_balance")
                    if old is not None and new is not None:
                        msg += f" balance: {old:.4f}→{new:.4f}"
                    if "cost_usd" in result:
                        msg += f" cost_usd={result['cost_usd']:.2f}"
                    if "proceeds_usd" in result:
                        msg += f" proceeds_usd={result['proceeds_usd']:.2f}"

                logger.info(msg)
                return result

            except Exception as e:
                # Логируем ошибку и пробрасываем дальше
                user_str = f"'{username}'" if username else "'unknown'"
                curr_str = f"'{currency}'" if currency else "'-'"
                amount_str = f"{amount:.4f}" if isinstance(amount, (int, float)) else "-"
                msg = (
                    f"{action} user={user_str} currency={curr_str} "
                    f"amount={amount_str} result=ERROR "
                    f"error_type='{type(e).__name__}' error_msg='{e}'"
                )
                logger.error(msg)
                raise

        return wrapper

    return decorator