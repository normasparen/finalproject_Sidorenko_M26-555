from typing import Dict

from valutatrade_hub.core.session import Session
from valutatrade_hub.core.usecase.portfolio import save_portfolio
from valutatrade_hub.core.usecase.rate import get_rate
from valutatrade_hub.core.utils.exceptions import SellError


def sell(currency: str, amount: float) -> Dict:
    if Session.current_user is None or Session.current_portfolio is None:
        raise SellError("Сначала выполните login")
    if not currency or not currency.strip():
        raise SellError("Некорректный код валюты")
    if amount is None or amount <= 0:
        raise SellError("'amount' должен быть положительным числом")

    code = currency.strip().upper()
    portfolio = Session.current_portfolio
    wallet = portfolio.get_wallet(code)
    if wallet is None:
        raise SellError(
            f"У вас нет кошелька '{code}'. Добавьте валюту: "
            f"она создаётся автоматически при первой покупке."
        )

    if amount > wallet.balance:
        raise SellError(
            f"Недостаточно средств: доступно {wallet.balance:.4f} {code}, "
            f"требуется {amount:.4f} {code}"
        )

    rate, _ = get_rate(code, "USD")
    if rate is None:
        raise SellError(f"Не удалось получить курс для {code}→USD")

    old_balance = wallet.balance
    wallet.withdraw(amount)
    proceeds_usd = amount * rate

    # начисляем эквивалент на usd
    usd_wallet = portfolio.get_wallet("USD")
    if usd_wallet is None:
        usd_wallet = portfolio.add_currency("USD")
    usd_wallet.deposit(proceeds_usd)

    save_portfolio(portfolio)

    return {
        "currency": code,
        "amount": amount,
        "rate": rate,
        "old_balance": old_balance,
        "new_balance": wallet.balance,
        "proceeds_usd": proceeds_usd,
    }
