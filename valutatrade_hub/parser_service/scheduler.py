import logging
import threading

from valutatrade_hub.parser_service.config import ParserConfig
from valutatrade_hub.parser_service.updater import RatesUpdater

logger = logging.getLogger("valutatrade.parser")


class RatesScheduler:
    """
    Планировщик для RatesUpdater
    """

    def __init__(self, interval_seconds: int = 300, config: ParserConfig | None = None):
        self.interval = interval_seconds
        self.updater = RatesUpdater(config)
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def _loop(self) -> None:
        logger.info(f"Scheduler started (interval={self.interval}s)")
        while not self._stop_event.is_set():
            try:
                logger.info("Scheduler: running update...")
                result = self.updater.run_update()
                logger.info(
                    f"Scheduler: status={result['status']}, "
                    f"rates={result['rates_count']}, "
                    f"error={result.get('error')}"
                )
            except Exception as e:
                logger.error(f"Scheduler: unexpected error: {e}")

            self._stop_event.wait(self.interval)

        logger.info("Scheduler stopped")

    def start(self) -> None:
        """Фоновый поток."""
        if self._thread and self._thread.is_alive():
            logger.warning("Scheduler already running")
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="RatesScheduler")
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)

    def run_forever(self) -> None:
        self.start()
        try:
            while True:
                threading.Event().wait(1)
        except KeyboardInterrupt:
            print("\nОстановка планировщика...")
            self.stop()