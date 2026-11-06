
from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.core.models.wallet import Wallet
from valutatrade_hub.core.usecase.rate import get_rate


class Portfolio:
    def __init__(self, user_id: int, wallets: dict[str, Wallet] | None = None):
        self._user_id = user_id
        self._wallets: dict[str, Wallet] = {}
        if wallets:
            for code, w in wallets.items():
                self._wallets[code.upper()] = w

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def wallets(self) -> dict[str, Wallet]:
        return dict(self._wallets)

    def add_currency(self, currency_code: str, initial_balance: float = 0.0) -> Wallet:
        currency = get_currency(currency_code)  # бросит CurrencyNotFoundError
        code = currency.code
        if code in self._wallets:
            raise ValueError(f"Кошелёк для валюты '{code}' уже существует.")
        wallet = Wallet(currency_code=code, balance=initial_balance)
        self._wallets[code] = wallet
        return wallet

    def get_wallet(self, currency_code: str) -> Wallet | None:
        if not currency_code:
            return None
        return self._wallets.get(currency_code.strip().upper())

    def get_total_value(self, base_currency: str = "USD") -> float:
        base = base_currency.strip().upper()
        total = 0.0
        for code, wallet in self._wallets.items():
            if code == base:
                total += wallet.balance
                continue
            rate, _ = get_rate(code, base)
            if rate:
                total += wallet.balance * rate
        return round(total, 8)

    def to_dict(self) -> dict:
        return {
            "user_id": self._user_id,
            "wallets": {c: {"balance": w.balance} for c, w in self._wallets.items()},
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Portfolio":
        wallets = {
            code: Wallet(currency_code=code, balance=info.get("balance", 0.0))
            for code, info in data.get("wallets", {}).items()
        }
        return cls(user_id=data["user_id"], wallets=wallets)