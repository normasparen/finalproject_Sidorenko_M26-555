from abc import ABC, abstractmethod
from typing import Dict
from valutatrade_hub.core.utils.exceptions import CurrencyNotFoundError


class Currency(ABC):
    def __init__(self, name: str, code: str):
        if not name or not name.strip():
            raise ValueError("Имя валюты не может быть пустым.")
        self.name = name.strip()

        # Валидация кода: верхний регистр, 2-5 символов, без пробелов
        code_clean = code.strip().upper()
        if not (2 <= len(code_clean) <= 5) or " " in code_clean:
            raise ValueError("Код валюты должен быть от 2 до 5 символов, без пробелов.")
        self.code = code_clean

    @abstractmethod
    def get_display_info(self) -> str:
        """Возвращает строковое представление для UI/логов."""
        pass


class FiatCurrency(Currency):
    def __init__(self, name: str, code: str, issuing_country: str):
        super().__init__(name, code)
        self.issuing_country = issuing_country

    def get_display_info(self) -> str:
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self.issuing_country})"


class CryptoCurrency(Currency):
    def __init__(self, name: str, code: str, algorithm: str, market_cap: float):
        super().__init__(name, code)
        self.algorithm = algorithm
        self.market_cap = market_cap

    def get_display_info(self) -> str:
        # Форматируем капитализацию в экспоненциальный вид (например, 1.12e12)
        mcap_str = f"{self.market_cap:.2e}"
        return f"[CRYPTO] {self.code} — {self.name} (Algo: {self.algorithm}, MCAP: {mcap_str})"


# --- Реестр валют (Фабрика) ---
_CURRENCY_REGISTRY: Dict[str, Currency] = {
    "USD": FiatCurrency("US Dollar", "USD", "United States"),
    "EUR": FiatCurrency("Euro", "EUR", "Eurozone"),
    "GBP": FiatCurrency("British Pound", "GBP", "United Kingdom"),
    "BTC": CryptoCurrency("Bitcoin", "BTC", "SHA-256", 1.12e12),
    "ETH": CryptoCurrency("Ethereum", "ETH", "Ethash", 3.8e11),
}


def get_currency(code: str) -> Currency:
    """Возвращает объект валюты по коду. Бросает CurrencyNotFoundError."""
    if not code:
        raise CurrencyNotFoundError("Неизвестная валюта ''")

    clean_code = code.strip().upper()
    if clean_code not in _CURRENCY_REGISTRY:
        raise CurrencyNotFoundError(f"Неизвестная валюта '{clean_code}'")

    return _CURRENCY_REGISTRY[clean_code]


def list_supported_codes() -> list[str]:
    return sorted(_CURRENCY_REGISTRY.keys())