from copy import deepcopy
from pathlib import Path
from typing import Any

from infrastructure.persistence.json_storage import JsonStorage


DEFAULT_CONFIG = {
    "settings": {
        "system": {
            "directory": "",
            "account_number": 3,
        },
        "general": {
            "appearance": {
                "language": "en",
                "theme": "dark",
                "show_id_section": True,
            },
            "behavior": {
                "minimize_on_apply": False,
                "preload_next_page": True,
            },
            "debug": {
                "debug_mode": False,
            },
        },
    },
    "wallpaper_metadata": {},
}


class ConfigRepository:
    def __init__(self, config_path: str | Path = "config.json"):
        self.storage = JsonStorage(config_path)

    def load(self) -> dict:
        loaded = self.storage.load(default=deepcopy(DEFAULT_CONFIG))
        return self._deep_merge(deepcopy(DEFAULT_CONFIG), loaded)

    def save(self, data: dict) -> bool:
        return self.storage.save(data)

    def _deep_merge(self, base: dict, override: dict) -> dict:
        result = deepcopy(base)

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result