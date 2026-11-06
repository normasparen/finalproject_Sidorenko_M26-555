from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.core.models.portfolio import Portfolio
from valutatrade_hub.core.session import Session
from valutatrade_hub.core.usecase.rate import get_rate
from valutatrade_hub.core.utils.decorators import log_action
from valutatrade_hub.core.utils.exceptions import BuyError, CurrencyNotFoundError
from valutatrade_hub.infra.database import db


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


@log_action("BUY", verbose=True)
def buy(currency: str, amount: float, **kwargs) -> dict:
    user = Session.get_current_user()
    if not user:
        raise BuyError("Сначала выполните login")

    try:
        currency_obj = get_currency(currency)
    except CurrencyNotFoundError as e:
        raise BuyError(str(e)) from e

    if amount is None or amount <= 0:
        raise BuyError("'amount' должен быть положительным числом")

    rate, _ = get_rate(currency_obj.code, "USD")
    if rate is None:
        raise BuyError(f"Не удалось получить курс для {currency_obj.code}→USD")

    portfolio = _load_portfolio(user.user_id)
    wallet = portfolio.get_wallet(currency_obj.code)
    if wallet is None:
        wallet = portfolio.add_currency(currency_obj.code)

    old_balance = wallet.balance
    wallet.deposit(amount)
    cost_usd = amount * rate

    # списываем usd
    usd_wallet = portfolio.get_wallet("USD")
    if usd_wallet is not None:
        try:
            usd_wallet.withdraw(cost_usd)
        except Exception as e:
            # откатываем
            wallet.withdraw(amount)
            raise BuyError(f"Недостаточно USD: требуется {cost_usd:.2f} USD") from e

    _save_portfolio(portfolio)

    return {
        "username": user.username,
        "currency": currency_obj.code,
        "amount": amount,
        "rate": rate,
        "old_balance": old_balance,
        "new_balance": wallet.balance,
        "cost_usd": cost_usd,
    }