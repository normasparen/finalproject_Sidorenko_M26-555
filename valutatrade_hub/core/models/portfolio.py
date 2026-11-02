import json
from typing import Optional, Dict

from . import User, Wallet


DEFAULT_EXCHANGE_RATES: Dict[str, float] = {
    "USD": 1.0,
    "EUR": 1.08,
    "GBP": 1.27,
    "BTC": 78000.0,
    "ETH": 3200.0,
    "RUB": 0.011,
}


class Portfolio:
    """"
    Класс портфеля
    """

    def __init__(self,
                 user_id: int,
                 wallets: Optional[Dict[str, Wallet]] = None,
                 exchange_rates: Optional[Dict[str, float]] = None):

        if not isinstance(user_id, int) or isinstance(user_id, bool):
            raise TypeError("user_id должен быть целым числом.")

        self._user_id = user_id
        self._wallets: Dict[str, Wallet] = {}

        if wallets:
            for code, wallet in wallets.items():
                if not isinstance(wallet, Wallet):
                    raise TypeError(f"Значение для '{code}' должно быть Wallet.")
                self._wallets[code.upper()] = wallet

        self._exchange_rates: Dict[str, float] = dict(
            exchange_rates if exchange_rates else DEFAULT_EXCHANGE_RATES
        )

        self._user: Optional[User] = None

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def user(self) -> Optional[User]:
        return self._user

    @user.setter
    def user(self, value: Optional[User]) -> None:
        """
        Сеттер юзера к портфелю
        """
        if value is not None and not isinstance(value, User):
            raise TypeError("user должен быть объектом User или None.")
        self._user = value

    @property
    def wallets(self) -> Dict[str, Wallet]:
        return dict(self._wallets)

    @property
    def exchange_rates(self) -> Dict[str, float]:
        return dict(self._exchange_rates)

    def add_currency(self, currency_code: str, initial_balance: float = 0.0) -> Wallet:
        """
        Добавляет новый кошелёк в портфель.
        """

        if not isinstance(currency_code, str) or not currency_code.strip():
            raise ValueError("Код валюты не может быть пустым.")
        code = currency_code.strip().upper()

        if code in self._wallets:
            raise ValueError(f"Кошелёк для валюты '{code}' уже существует.")

        wallet = Wallet(currency_code=code, balance=initial_balance)
        self._wallets[code] = wallet
        print(f"Добавлен кошелёк {code} с балансом {wallet.balance}.")
        return wallet

    def get_wallet(self, currency_code: str) -> Optional[Wallet]:
        """
        Возвращает объект кошелька по коду валюты.
        """
        if not isinstance(currency_code, str):
            return None
        return self._wallets.get(currency_code.strip().upper())

    def _convert_to_base(self, amount: float, currency_code: str,
                         base_currency: str) -> float:
        """
        Конвертирует сумму
        """

        code = currency_code.upper()
        base = base_currency.upper()

        if code not in self._exchange_rates:
            raise ValueError(f"Курс для валюты '{code}' не задан.")
        if base not in self._exchange_rates:
            raise ValueError(f"Курс для валюты '{base}' не задан.")

        amount_in_usd = amount * self._exchange_rates[code]
        return amount_in_usd / self._exchange_rates[base]

    def get_total_value(self, base_currency: str = "USD") -> float:
        """
        Возвращает общую стоимость всех валют в указанной валюте
        """
        base = base_currency.strip().upper()
        if base not in self._exchange_rates:
            raise ValueError(f"Курс для базовой валюты '{base}' не задан.")

        total = 0.0
        for code, wallet in self._wallets.items():
            total += self._convert_to_base(wallet.balance, code, base)
        return round(total, 8)

    def get_total_value_info(self, base_currency: str = "USD") -> dict:
        """Выводит информацию об общей стоимости и возвращает словарь."""
        total = self.get_total_value(base_currency)
        print(f"Общая стоимость портфеля пользователя {self._user_id} "
              f"в {base_currency.upper()}: {total}")
        return {"user_id": self._user_id,
                "base_currency": base_currency.upper(),
                "total_value": total}

    def buy_currency(self, currency_code: str, amount: float,
                     exchange_rates: Optional[Dict[str, float]] = None) -> bool:
        """
        Покупка валюты: сумма списывается с usd - кошелька.
        """
        code = currency_code.strip().upper()
        if code == "USD":
            print("Нельзя купить USD за USD.")
            return False

        usd_wallet = self.get_wallet("USD")
        target_wallet = self.get_wallet(code)
        if usd_wallet is None:
            raise ValueError("Отсутствует USD-кошелёк для списания средств.")
        if target_wallet is None:
            target_wallet = self.add_currency(code)

        rates = exchange_rates or self._exchange_rates
        if code not in rates:
            raise ValueError(f"Курс для валюты '{code}' не задан.")

        cost_usd = amount * rates[code]
        if not usd_wallet.withdraw(cost_usd):
            return False

        target_wallet.deposit(amount)
        print(f"Куплено {amount} {code} за {cost_usd} USD.")
        return True

    def sell_currency(self, currency_code: str, amount: float,
                      exchange_rates: Optional[Dict[str, float]] = None) -> bool:
        """
        Продажа валюты: сумма начисляется на usd - кошелёк.
        """
        code = currency_code.strip().upper()
        if code == "USD":
            print("Нельзя продать USD за USD.")
            return False

        usd_wallet = self.get_wallet("USD")
        target_wallet = self.get_wallet(code)
        if target_wallet is None:
            print(f"Кошелька для валюты '{code}' нет.")
            return False
        if usd_wallet is None:
            usd_wallet = self.add_currency("USD")

        rates = exchange_rates or self._exchange_rates
        if code not in rates:
            raise ValueError(f"Курс для валюты '{code}' не задан.")

        if not target_wallet.withdraw(amount):
            return False

        proceeds_usd = amount * rates[code]
        usd_wallet.deposit(proceeds_usd)
        print(f"Продано {amount} {code} за {proceeds_usd} USD.")
        return True

    def to_dict(self) -> dict:
        """Преобразует портфель в словарь"""
        return {
            "user_id": self._user_id,
            "wallets": {
                code: {"balance": wallet.balance}
                for code, wallet in self._wallets.items()
            },
        }

