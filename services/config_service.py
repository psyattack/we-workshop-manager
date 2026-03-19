from pathlib import Path
from typing import Any, Optional

from infrastructure.persistence.config_repository import ConfigRepository
from shared.filesystem import get_app_data_dir


class ConfigService:
    def __init__(self, config_path: str | Path | None = None):
        if config_path is None:
            config_path = get_app_data_dir() / "config.json"
        self.repository = ConfigRepository(config_path)
        self.config = self.repository.load()

    def reload(self) -> None:
        self.config = self.repository.load()

    def save(self) -> bool:
        return self.repository.save(self.config)

    def get(self, key: str, default: Any = None) -> Any:
        value = self.config
        for part in key.split("."):
            if not isinstance(value, dict):
                return default
            value = value.get(part)
            if value is None:
                return default
        return value

    def set(self, key: str, value: Any) -> None:
        parts = key.split(".")
        current = self.config
        for part in parts[:-1]:
            existing = current.get(part)
            if not isinstance(existing, dict):
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value
        self.save()

    def remove(self, key: str) -> None:
        parts = key.split(".")
        current = self.config
        for part in parts[:-1]:
            if not isinstance(current, dict):
                return
            current = current.get(part)
            if current is None:
                return
        if isinstance(current, dict) and parts[-1] in current:
            del current[parts[-1]]
            self.save()

    def get_directory(self) -> str:
        return self.get("settings.system.directory", "")

    def set_directory(self, path: str) -> None:
        self.set("settings.system.directory", path)

    def get_account_number(self) -> int:
        return self.get("settings.account.account.account_number", 3)

    def set_account_number(self, number: int) -> None:
        self.set("settings.account.account.account_number", number)

    def get_language(self) -> str:
        return self.get("settings.general.appearance.language", "en")

    def set_language(self, language: str) -> None:
        self.set("settings.general.appearance.language", language)

    def get_theme(self) -> str:
        return self.get("settings.general.appearance.theme", "dark")

    def set_theme(self, theme: str) -> None:
        self.set("settings.general.appearance.theme", theme)

    def get_show_id_section(self) -> bool:
        return self.get("settings.general.appearance.show_id_section", True)

    def set_show_id_section(self, value: bool) -> None:
        self.set("settings.general.appearance.show_id_section", value)

    def get_minimize_on_apply(self) -> bool:
        return self.get("settings.general.behavior.minimize_on_apply", False)

    def set_minimize_on_apply(self, value: bool) -> None:
        self.set("settings.general.behavior.minimize_on_apply", value)

    def get_preload_next_page(self) -> bool:
        return self.get("settings.general.behavior.preload_next_page", True)

    def set_preload_next_page(self, value: bool) -> None:
        self.set("settings.general.behavior.preload_next_page", value)

    def get_auto_check_updates(self) -> bool:
        return self.get("settings.general.behavior.auto_check_updates", True)

    def set_auto_check_updates(self, value: bool) -> None:
        self.set("settings.general.behavior.auto_check_updates", value)

    def get_skip_version(self) -> str:
        return self.get("settings.general.behavior.skip_version", "")

    def set_skip_version(self, value: str) -> None:
        self.set("settings.general.behavior.skip_version", value)

    def get_save_window_state(self) -> bool:
        return self.get("settings.general.behavior.save_window_state", True)

    def set_save_window_state(self, value: bool) -> None:
        self.set("settings.general.behavior.save_window_state", value)

    def get_window_geometry(self) -> dict:
        return self.get(
            "settings.general.behavior.window_geometry",
            {
                "x": -1,
                "y": -1,
                "width": 1200,
                "height": 730,
                "is_maximized": False,
            },
        )

    def set_window_geometry(self, x: int, y: int, width: int, height: int, is_maximized: bool) -> None:
        self.set(
            "settings.general.behavior.window_geometry",
            {
                "x": x,
                "y": y,
                "width": width,
                "height": height,
                "is_maximized": is_maximized,
            },
        )

    def get_debug_mode(self) -> bool:
        return self.get("settings.advanced.debug.debug_mode", False)

    def set_debug_mode(self, value: bool) -> None:
        self.set("settings.advanced.debug.debug_mode", value)

    def get_wallpaper_metadata(self, pubfileid: str) -> Optional[dict]:
        metadata = self.get("wallpaper_metadata", {})
        if not isinstance(metadata, dict):
            return None
        return metadata.get(pubfileid)

    def get_all_wallpaper_metadata(self) -> dict[str, dict]:
        metadata = self.get("wallpaper_metadata", {})
        if not isinstance(metadata, dict):
            return {}
        return metadata

    def set_wallpaper_metadata(self, pubfileid: str, data: dict) -> None:
        metadata = self.get("wallpaper_metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}
        metadata[pubfileid] = data
        self.set("wallpaper_metadata", metadata)

    def remove_wallpaper_metadata(self, pubfileid: str) -> None:
        metadata = self.get("wallpaper_metadata", {})
        if not isinstance(metadata, dict):
            return
        if pubfileid in metadata:
            del metadata[pubfileid]
            self.set("wallpaper_metadata", metadata)

    def get_background_image(self, area: str) -> str:
        return self.get(f"settings.backgrounds.{area}.image", "")

    def set_background_image(self, area: str, b64: str) -> None:
        self.set(f"settings.backgrounds.{area}.image", b64)

    def get_background_blur(self, area: str) -> int:
        return self.get(f"settings.backgrounds.{area}.blur", 0)

    def set_background_blur(self, area: str, v: int) -> None:
        self.set(f"settings.backgrounds.{area}.blur", v)

    def get_background_opacity(self, area: str) -> int:
        return self.get(f"settings.backgrounds.{area}.opacity", 100)

    def set_background_opacity(self, area: str, v: int) -> None:
        self.set(f"settings.backgrounds.{area}.opacity", v)

    def get_background_extend_titlebar(self) -> bool:
        return self.get("settings.backgrounds.extend_to_titlebar", False)

    def set_background_extend_titlebar(self, v: bool) -> None:
        self.set("settings.backgrounds.extend_to_titlebar", v)