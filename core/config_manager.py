import json
from pathlib import Path
from typing import Any, Optional

class ConfigManager:
    DEFAULT_CONFIG = {
        "directory": "",
        "account_number": 3,
        "theme": "dark",
        "language": "en"
    }
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self.config = self.load()
    
    def load(self) -> dict:
        if not self.config_path.exists():
            return self.DEFAULT_CONFIG.copy()
        
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)

                config = self.DEFAULT_CONFIG.copy()
                config.update(loaded)
                return config
        except Exception as e:
            print(f"Error loading config: {e}")
            return self.DEFAULT_CONFIG.copy()
    
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
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self.save()
    
    def get_directory(self) -> str:
        return self.get("directory", "")
    
    def set_directory(self, path: str) -> None:
        self.set("directory", path)
    
    def get_account_number(self) -> int:
        return self.get("account_number", 3)
    
    def set_account_number(self, number: int) -> None:
        self.set("account_number", number)
    
    def get_theme(self) -> str:
        return self.get("theme", "dark")
    
    def set_theme(self, theme: str) -> None:
        self.set("theme", theme)
    
    def get_language(self) -> str:
        return self.get("language", "en")
    
    def set_language(self, lang: str) -> None:
        self.set("language", lang)
    
    def get_custom_background(self) -> Optional[str]:
        return self.get("custom_background")
    
    def set_custom_background(self, base64_data: Optional[str]) -> None:
        if base64_data:
            self.set("custom_background", base64_data)
        elif "custom_background" in self.config:
            del self.config["custom_background"]
            self.save()