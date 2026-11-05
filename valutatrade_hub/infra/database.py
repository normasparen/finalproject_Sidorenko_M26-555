import json
import os
from typing import Any, Dict, List

from valutatrade_hub.infra.settings import SettingsLoader


class DatabaseManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, data_dir: str | None = None):
        if getattr(self, "_initialized", False):
            return
        self.data_dir = data_dir or SettingsLoader().get("DATA_DIR", "data")
        os.makedirs(self.data_dir, exist_ok=True)
        self._initialized = True

    def _path(self, filename: str) -> str:
        return os.path.join(self.data_dir, filename)

    def _load_json(self, filename: str, default: Any) -> Any:
        path = self._path(filename)
        if not os.path.exists(path):
            return default
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                return json.loads(content) if content else default
        except (json.JSONDecodeError, OSError):
            return default

    def _save_json(self, filename: str, data: Any) -> None:
        path = self._path(filename)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)

    # ---- users ----
    def load_users(self) -> List[Dict]:
        return self._load_json("users.json", [])

    def save_users(self, users: List[Dict]) -> None:
        self._save_json("users.json", users)

    # ---- portfolios ----
    def load_portfolios(self) -> List[Dict]:
        return self._load_json("portfolios.json", [])

    def save_portfolios(self, portfolios: List[Dict]) -> None:
        self._save_json("portfolios.json", portfolios)

    # ---- rates ----
    def load_rates(self) -> Dict:
        return self._load_json("rates.json", {})

    def save_rates(self, rates: Dict) -> None:
        self._save_json("rates.json", rates)


# Удобный глобальный экземпляр
db = DatabaseManager()