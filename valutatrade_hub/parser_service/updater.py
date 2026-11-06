import logging

from valutatrade_hub.core.utils.exceptions import ApiRequestError
from valutatrade_hub.parser_service.api_client import (
    CoinGeckoClient,
    ExchangeRateApiClient,
)
from valutatrade_hub.parser_service.config import ParserConfig
from valutatrade_hub.parser_service.storage import ParserStorage

logger = logging.getLogger("valutatrade.parser")


class RatesUpdater:
    """Координирует опрос всех клиентов и сохранение результата."""

    def __init__(self, config: ParserConfig | None = None):
        self.config = config or ParserConfig()
        self.clients = {
            "CoinGecko": CoinGeckoClient(self.config),
            "ExchangeRate-API": ExchangeRateApiClient(self.config),
        }
        self.storage = ParserStorage(
            rates_path=self.config.RATES_FILE_PATH,
            history_path=self.config.HISTORY_FILE_PATH,
        )

    def run_update(self) -> dict:
        logger.info("Starting rates update...")
        all_rates: dict[str, float] = {}
        errors = []

        for name, client in self.clients.items():
            logger.info(f"Fetching from {name}...")
            try:
                rates = client.fetch_rates()
                all_rates.update(rates)
                logger.info(f"{name}: OK ({len(rates)} rates)")
            except ApiRequestError as e:
                logger.error(f"Failed to fetch from {name}: {e}")
                errors.append(f"{name}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error from {name}: {e}")
                errors.append(f"{name}: unexpected error")

        if not all_rates:
            return {
                "status": "error",
                "rates_count": 0,
                "last_refresh": None,
                "error": "; ".join(errors) if errors else "No rates received",
            }

        # Обновляем rates.json
        logger.info(f"Writing {len(all_rates)} rates to {self.config.RATES_FILE_PATH}")
        self.storage.update_rates_snapshot(all_rates, source="ParserService")

        # Пишем историю
        for name in self.clients:
            client_rates = {
                k: v for k, v in all_rates.items()
                if (name == "CoinGecko" and k.split("_")[0] in self.config.CRYPTO_ID_MAP)
                or (name == "ExchangeRate-API" and k.split("_")[0] in self.config.FIAT_CURRENCIES)
            }
            if client_rates:
                added = self.storage.append_history(client_rates, source=name)
                logger.info(f"History updated for {name} (+{added} records)")

        last_refresh = self.storage.get_rates_snapshot().get("last_refresh")
        status = "ok" if not errors else "partial"
        return {
            "status": status,
            "rates_count": len(all_rates),
            "last_refresh": last_refresh,
            "error": "; ".join(errors) if errors else None,
        }