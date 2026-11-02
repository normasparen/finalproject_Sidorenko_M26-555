from typing import Dict

from valutatrade_hub.core.session import Session
from valutatrade_hub.core.usecase.portfolio import save_portfolio
from valutatrade_hub.core.usecase.rate import get_rate
from valutatrade_hub.core.utils.exceptions import BuyError


def buy(currency: str, amount: float) -> Dict:

    if Session.current_user is None or Session.current_portfolio is None:
        raise BuyError("Сначала выполните login")
    if not currency or not currency.strip():

        raise BuyError("Некорректный код валюты")
    if amount is None or amount <= 0:
        raise BuyError("'amount' должен быть положительным числом")

    code = currency.strip().upper()
    rate, _ = get_rate(code, "USD")
    if rate is None:
        raise BuyError(f"Не удалось получить курс для {code}→USD")

    portfolio = Session.current_portfolio
    wallet = portfolio.get_wallet(code)

    if wallet is None:
        wallet = portfolio.add_currency(code)

    old_balance = wallet.balance
    wallet.deposit(amount)

    save_portfolio(portfolio)
    cost_usd = amount * rate

    return {
        "currency": code,
        "amount": amount,
        "rate": rate,
        "old_balance": old_balance,
        "new_balance": wallet.balance,
        "cost_usd": cost_usd,
    }




