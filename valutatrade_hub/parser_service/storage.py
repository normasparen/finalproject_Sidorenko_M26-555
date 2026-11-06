import json
import os
from datetime import UTC, datetime


class ParserStorage:
    """Хранилище парсера"""

    def __init__(self, rates_path: str, history_path: str):
        self.rates_path = rates_path
        self.history_path = history_path

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")

    @staticmethod
    def _safe_load(path: str, default):
        if not os.path.exists(path):
            return default
        try:
            with open(path, encoding="utf-8") as f:
                content = f.read().strip()
                return json.loads(content) if content else default
        except (json.JSONDecodeError, OSError):
            return default

    @staticmethod
    def _atomic_write(path: str, data) -> None:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)

    def append_history(self, rates: dict[str, float], source: str, meta: dict = None) -> int:
        """Добавляет записи в exchange_rates.json."""
        history: list[dict] = self._safe_load(self.history_path, [])
        if not isinstance(history, list):
            history = []

        existing_ids = {item.get("id") for item in history if isinstance(item, dict)}
        now = self._now_iso()
        added = 0

        for pair, rate in rates.items():
            try:
                from_c, to_c = pair.split("_", 1)
            except ValueError:
                continue

            record_id = f"{from_c}_{to_c}_{now}"
            if record_id in existing_ids:
                continue

            record = {
                "id": record_id,
                "from_currency": from_c,
                "to_currency": to_c,
                "rate": float(rate),
                "timestamp": now,
                "source": source,
                "meta": meta or {},
            }
            history.append(record)
            existing_ids.add(record_id)
            added += 1

        if added:
            self._atomic_write(self.history_path, history)
        return added

    def update_rates_snapshot(self, rates: dict[str, float], source: str) -> None:

        snapshot = self._safe_load(self.rates_path, {})
        if not isinstance(snapshot, dict):
            snapshot = {}

        now = self._now_iso()
        for pair, rate in rates.items():
            snapshot[pair] = {
                "rate": float(rate),
                "updated_at": now,
                "source": source,
            }
        snapshot["last_refresh"] = now
        self._atomic_write(self.rates_path, snapshot)

    def get_rates_snapshot(self) -> dict:
        return self._safe_load(self.rates_path, {})