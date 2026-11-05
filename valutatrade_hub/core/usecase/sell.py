from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.core.models.portfolio import Portfolio
from valutatrade_hub.core.usecase.rate import get_rate
from valutatrade_hub.core.session import Session
from valutatrade_hub.core.utils.exceptions import (
    SellError, CurrencyNotFoundError, InsufficientFundsError,
)
from valutatrade_hub.infra.database import db
from valutatrade_hub.decorators import log_action


def _load_portfolio(user_id: int) -> Portfolio:
    for p in db.load_portfolios():
        if p["user_id"] == user_id:
            return Portfolio.from_dict(p)
    return Portfolio(user_id=user_id)


def _save_portfolio(portfolio: Portfolio) -> None:
    portfolios = db.load_portfolios()
    data = portfolio.to_dict()
    for i, p in enumerate(portfolios):
        if p["user_id"] == data["user_id"]:
            portfolios[i] = data
            break
    else:
        portfolios.append(data)
    db.save_portfolios(portfolios)


@log_action("SELL", verbose=True)
def sell(currency: str, amount: float, **kwargs) -> dict:
    user = Session.get_current_user()
    if not user:
        raise SellError("Сначала выполните login")

    try:
        currency_obj = get_currency(currency)
    except CurrencyNotFoundError as e:
        raise SellError(str(e))

    if amount is None or amount <= 0:
        raise SellError("'amount' должен быть положительным числом")

    portfolio = _load_portfolio(user.user_id)
    wallet = portfolio.get_wallet(currency_obj.code)
    if wallet is None:
        raise SellError(
            f"У вас нет кошелька '{currency_obj.code}'. "
            "Добавьте валюту: она создаётся автоматически при первой покупке."
        )

    rate, _ = get_rate(currency_obj.code, "USD")
    if rate is None:
        raise SellError(f"Не удалось получить курс для {currency_obj.code}→USD")

    old_balance = wallet.balance
    try:
        wallet.withdraw(amount)
    except InsufficientFundsError as e:
        raise SellError(str(e))

    proceeds_usd = amount * rate
    usd_wallet = portfolio.get_wallet("USD")
    if usd_wallet is None:
        usd_wallet = portfolio.add_currency("USD")
    usd_wallet.deposit(proceeds_usd)

    _save_portfolio(portfolio)
    return {
        "currency": currency_obj.code,
        "amount": amount,
        "rate": rate,
        "old_balance": old_balance,
        "new_balance": wallet.balance,
        "proceeds_usd": proceeds_usd,
    }