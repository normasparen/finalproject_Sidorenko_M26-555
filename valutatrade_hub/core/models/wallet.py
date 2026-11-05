

class Wallet:
    def __init__(self, currency_code: str, balance: float = 0.0):
        if not isinstance(currency_code, str) or not currency_code.strip():
            raise ValueError("Код валюты не может быть пустым.")
        self.currency_code = currency_code.strip().upper()
        self._balance = 0.0
        self.balance = balance

    @property
    def balance(self) -> float:
        return self._balance

    @balance.setter
    def balance(self, value: float) -> None:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise TypeError("Баланс должен быть числом.")
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным.")
        self._balance = float(value)

    @staticmethod
    def _validate_amount(amount: float) -> float:
        if not isinstance(amount, (int, float)) or isinstance(amount, bool):
            raise TypeError("Сумма должна быть числом.")
        if amount <= 0:
            raise ValueError("Сумма должна быть положительным числом.")
        return float(amount)

    def deposit(self, amount: float) -> None:
        amount = self._validate_amount(amount)
        self._balance += amount

    def withdraw(self, amount: float) -> bool:
        from valutatrade_hub.core.utils.exceptions import InsufficientFundsError
        amount = self._validate_amount(amount)
        if amount > self._balance:
            raise InsufficientFundsError(self._balance, amount, self.currency_code)
        self._balance -= amount
        return True

    def get_balance_info(self) -> dict:
        info = {"currency_code": self.currency_code, "balance": self._balance}
        print(f"Валюта: {self.currency_code} | Баланс: {self._balance}")
        return info

    def to_dict(self) -> dict:
        return {"currency_code": self.currency_code, "balance": self._balance}

    @classmethod
    def from_dict(cls, data: dict) -> "Wallet":
        return cls(currency_code=data["currency_code"], balance=data.get("balance", 0.0))