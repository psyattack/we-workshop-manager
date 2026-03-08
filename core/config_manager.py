import json
from pathlib import Path
from typing import Any, Optional, Dict

class ConfigManager:
    DEFAULT_CONFIG = {
        "settings": {
            "system": {
                "directory": "",
                "account_number": 3
            },
            "general": {
                "appearance": {
                    "language": "en",
                    "theme": "dark"
                },
                "behavior": {
                    "minimize_on_apply": False,
                    "preload_next_page": True
                }
            }
        },
        "wallpaper_metadata": {}
    }

    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self.config = self.load()

    def _deep_merge(self, base: dict, override: dict) -> dict:
        result = base.copy()
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

    def load(self) -> dict:
        if not self.config_path.exists():
            return json.loads(json.dumps(self.DEFAULT_CONFIG))

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                return self._deep_merge(
                    json.loads(json.dumps(self.DEFAULT_CONFIG)), loaded
                )
        except Exception as e:
            print(f"Error loading config: {e}")
            return json.loads(json.dumps(self.DEFAULT_CONFIG))

    def save(self) -> bool:
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value if value is not None else default

    def set(self, key: str, value: Any) -> None:
        keys = key.split(".")
        config = self.config

        for k in keys[:-1]:
            if k not in config or not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value
        self.save()

    def get_directory(self) -> str:
        return self.get("settings.system.directory", "")

    def set_directory(self, path: str) -> None:
        self.set("settings.system.directory", path)

    def get_account_number(self) -> int:
        return self.get("settings.system.account_number", 4)

    def set_account_number(self, number: int) -> None:
        self.set("settings.system.account_number", number)

    def get_language(self) -> str:
        return self.get("settings.general.appearance.language", "en")

    def set_language(self, lang: str) -> None:
        self.set("settings.general.appearance.language", lang)

    def get_theme(self) -> str:
        return self.get("settings.general.appearance.theme", "dark")

    def set_theme(self, theme: str) -> None:
        self.set("settings.general.appearance.theme", theme)

    def get_minimize_on_apply(self) -> bool:
        return self.get("settings.general.behavior.minimize_on_apply", False)

    def set_minimize_on_apply(self, value: bool) -> None:
        self.set("settings.general.behavior.minimize_on_apply", value)

    def get_preload_next_page(self) -> bool:
        return self.get("settings.general.behavior.preload_next_page", True)

    def set_preload_next_page(self, value: bool) -> None:
        self.set("settings.general.behavior.preload_next_page", value)

    def get_wallpaper_metadata(self, pubfileid: str) -> Optional[Dict]:
        metadata = self.get("wallpaper_metadata", {})
        return metadata.get(pubfileid)

    def set_wallpaper_metadata(self, pubfileid: str, data: Dict) -> None:
        metadata = self.get("wallpaper_metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}
        metadata[pubfileid] = data
        self.set("wallpaper_metadata", metadata)

    def remove_wallpaper_metadata(self, pubfileid: str) -> None:
        metadata = self.get("wallpaper_metadata", {})
        if isinstance(metadata, dict) and pubfileid in metadata:
            del metadata[pubfileid]
            self.set("wallpaper_metadata", metadata)

    def get_all_wallpaper_metadata(self) -> Dict[str, Dict]:
        metadata = self.get("wallpaper_metadata", {})
        return metadata if isinstance(metadata, dict) else {}
