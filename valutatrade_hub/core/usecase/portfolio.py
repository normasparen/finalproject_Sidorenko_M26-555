from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.core.models.portfolio import Portfolio
from valutatrade_hub.core.session import Session
from valutatrade_hub.core.usecase.rate import get_rate
from valutatrade_hub.core.utils.exceptions import CurrencyNotFoundError, PortfolioError
from valutatrade_hub.infra.database import db


def show_portfolio(base: str = "USD") -> dict:
    user = Session.get_current_user()
    if not user:
        raise PortfolioError("Сначала выполните login")

    try:
        base_currency = get_currency(base)
    except CurrencyNotFoundError:
        raise PortfolioError(f"Неизвестная базовая валюта '{base}'")

    portfolio = None
    for p in db.load_portfolios():
        if p["user_id"] == user.user_id:
            portfolio = Portfolio.from_dict(p)
            break
    if portfolio is None:
        portfolio = Portfolio(user_id=user.user_id)

    wallets = portfolio.wallets
    if not wallets:
        return {"username": user.username, "base": base_currency.code,
                "wallets": [], "total": 0.0}

    rows, total = [], 0.0
    for code, w in wallets.items():
        if code == base_currency.code:
            value = w.balance
        else:
            rate, _ = get_rate(code, base_currency.code)
            value = w.balance * rate if rate else None

        if value is not None:
            total += value
        rows.append({"currency": code, "balance": w.balance,
                     "value_in_base": value})

    return {"username": user.username, "base": base_currency.code,
            "wallets": rows, "total": total}