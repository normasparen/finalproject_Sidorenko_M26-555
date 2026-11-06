import time

import requests

from valutatrade_hub.core.utils.exceptions import ApiRequestError
from valutatrade_hub.parser_service.config import ParserConfig


class BaseApiClient:
    """Абстрактный клиент для получения курсов."""

    def fetch_rates(self) -> dict[str, float]:
        raise NotImplementedError


class CoinGeckoClient(BaseApiClient):
    """
    Клиент CoinGecko, криптовалюты
    """

    def __init__(self, config: ParserConfig | None = None):
        self.config = config or ParserConfig()

    def _build_url(self) -> str:
        ids = list(self.config.CRYPTO_ID_MAP.values())
        params = {
            "ids": ",".join(ids),
            "vs_currencies": self.config.BASE_CURRENCY.lower(),
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.config.COINGECKO_URL}?{query}"

    def fetch_rates(self) -> dict[str, float]:
        url = self._build_url()
        last_error: Exception | None = None

        for _attempt in range(1, self.config.MAX_RETRIES + 1):
            try:
                response = requests.get(url, timeout=self.config.REQUEST_TIMEOUT)
                response.raise_for_status()
                data = response.json()
                return self._parse(data)
            except requests.exceptions.RequestException as e:
                last_error = e
                time.sleep(1)

        raise ApiRequestError(f"CoinGecko: {last_error}")

    def _parse(self, data: dict) -> dict[str, float]:
        id_to_ticker = {v: k for k, v in self.config.CRYPTO_ID_MAP.items()}
        result: dict[str, float] = {}
        base = self.config.BASE_CURRENCY.upper()

        for coin_id, rates in data.items():
            ticker = id_to_ticker.get(coin_id)
            if not ticker:
                continue
            for vs_currency, rate in rates.items():
                if vs_currency.upper() == base:
                    result[f"{ticker}_{base}"] = float(rate)
        return result


class ExchangeRateApiClient(BaseApiClient):
    """
    Клиент ExchangeRate-API, фиат
    """

    def __init__(self, config: ParserConfig | None = None):
        self.config = config or ParserConfig()

    def _build_url(self) -> str:
        key = self.config.EXCHANGERATE_API_KEY
        base = self.config.BASE_CURRENCY
        return f"{self.config.EXCHANGERATE_API_URL}/{key}/latest/{base}"

    def fetch_rates(self) -> dict[str, float]:
        if not self.config.EXCHANGERATE_API_KEY:
            raise ApiRequestError("ExchangeRate-API: не задан API-ключ (EXCHANGERATE_API_KEY)")

        url = self._build_url()
        last_error: Exception | None = None

        for _attempt in range(1, self.config.MAX_RETRIES + 1):
            try:
                response = requests.get(url, timeout=self.config.REQUEST_TIMEOUT)
                if response.status_code == 429:
                    raise ApiRequestError("ExchangeRate-API: превышен лимит запросов (429)")
                response.raise_for_status()
                data = response.json()
                return self._parse(data)
            except requests.exceptions.RequestException as e:
                last_error = e
                time.sleep(1)

        raise ApiRequestError(f"ExchangeRate-API: {last_error}")

    def _parse(self, data: dict) -> dict[str, float]:
        if data.get("result") != "success":
            raise ApiRequestError(f"ExchangeRate-API: "
                                  f"ответ с ошибкой: {data.get('error-type', 'unknown')}")

        rates = data.get("conversion_rates", {})
        base = data.get("base_code", self.config.BASE_CURRENCY)
        result: dict[str, float] = {}

        for code in self.config.FIAT_CURRENCIES:
            if code in rates:

                rate_value = rates[code]
                if rate_value > 0:
                    result[f"{code}_{base}"] = 1.0 / rate_value

        return result