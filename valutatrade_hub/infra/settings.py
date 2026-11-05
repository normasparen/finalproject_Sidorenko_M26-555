import json
import os
from typing import Any, Optional

class SettingsLoader:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SettingsLoader, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_path: str = "config.json"):
        if self._initialized:
            return
        self._config_path = config_path
        self._config = {}
        self.reload()
        self._initialized = True

    def reload(self) -> None:

        if os.path.exists(self._config_path):
            with open(self._config_path, "r", encoding="utf-8") as f:
                self._config = json.load(f)
        else:
            self._config = {
                "RATES_TTL_SECONDS": 300,
                "BASE_CURRENCY": "USD",
                "LOG_FILE": "logs/actions.log",
                "DATA_DIR": "data"
            }

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)