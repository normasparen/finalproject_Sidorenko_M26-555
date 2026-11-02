import json


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
        """
        Устанавливает баланс с проверкой типа и неотрицательности.
        """
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
        print(f"[{self.currency_code}] Пополнение на {amount}. "
              f"Текущий баланс: {self._balance}")

    def withdraw(self, amount: float) -> bool:
        amount = self._validate_amount(amount)
        if amount > self._balance:
            print(f"[{self.currency_code}] Недостаточно средств. "
                  f"Запрошено: {amount}, доступно: {self._balance}")
            return False

        self._balance -= amount
        print(f"[{self.currency_code}] Снятие {amount}. "
              f"Текущий баланс: {self._balance}")
        return True

    def get_balance_info(self) -> dict:
        info = {
            "currency_code": self.currency_code,
            "balance": self._balance,
        }
        print(f"Валюта: {self.currency_code} | Баланс: {self._balance}")
        return info
