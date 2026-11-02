from typing import Dict

from valutatrade_hub.core import storage
from valutatrade_hub.core.models import Wallet, Portfolio
from valutatrade_hub.core.session import Session
from valutatrade_hub.core.usecase.rate import get_rate
from valutatrade_hub.core.utils.exceptions import PortfolioError


def show_portfolio(base: str = "USD") -> Dict:
    if Session.current_user is None or Session.current_portfolio is None:
        raise PortfolioError("Сначала выполните login")

    base = base.strip().upper()
    if get_rate(base, "USD") is None:
        raise PortfolioError(f"Неизвестная базовая валюта '{base}'")

    portfolio = Session.current_portfolio
    wallets = portfolio.wallets

    if not wallets:
        return {
            "username": Session.current_user.username,
            "base": base,
            "wallets": [],
            "total": 0.0,
        }

    rows = []
    total = 0.0
    for code, wallet in wallets.items():
        rate, _ = get_rate(code, base)
        if rate is None:
            value = None
        else:
            value = wallet.balance * rate
            total += value
        rows.append({"currency": code, "balance": wallet.balance,
                     "value_in_base": value})

    return {
        "username": Session.current_user.username,
        "base": base,
        "wallets": rows,
        "total": total,
    }

def load_portfolio_for_user(user_id: int) -> Portfolio:
    portfolios = storage.load_portfolios()
    for p in portfolios:
        if p["user_id"] == user_id:
            wallets = {}
            for code, info in p.get("wallets", {}).items():
                wallets[code] = Wallet(code, info.get("balance", 0.0))
            return Portfolio(user_id=user_id, wallets=wallets)

    portfolios.append({"user_id": user_id, "wallets": {}})
    storage.save_portfolios(portfolios)
    return Portfolio(user_id=user_id)


def save_portfolio(portfolio: Portfolio) -> None:
    """Сохраняет объект портфеля обратно в json."""
    portfolios = storage.load_portfolios()
    data = portfolio.to_dict()
    for i, p in enumerate(portfolios):
        if p["user_id"] == data["user_id"]:
            portfolios[i] = data
            break
    else:
        portfolios.append(data)
    storage.save_portfolios(portfolios)