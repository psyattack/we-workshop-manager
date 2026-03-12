import json
from pathlib import Path
from typing import Any


class TranslationService:
    SUPPORTED_LANGUAGES = {
        "de": "Deutsch",
        "en": "English",
        "es": "Español",
        "fr": "Français",
        "ja": "日本語",
        "pt": "Português",
        "ru": "Русский",
        "zh": "中文",
    }

    def __init__(self, language: str = "en"):
        self.current_language = language
        self.translations: dict[str, dict] = {}
        self._load_translations()

    def _load_translations(self) -> None:
        localization_dir = Path(__file__).resolve().parent.parent / "localization"

        for language_code in self.SUPPORTED_LANGUAGES.keys():
            file_path = localization_dir / f"{language_code}.json"
            if not file_path.exists():
                self.translations[language_code] = {}
                continue

            try:
                with file_path.open("r", encoding="utf-8") as file:
                    self.translations[language_code] = json.load(file)
            except Exception:
                self.translations[language_code] = {}

    def set_language(self, language: str) -> None:
        if language in self.SUPPORTED_LANGUAGES:
            self.current_language = language

    def get_language(self) -> str:
        return self.current_language

    def get_available_languages(self) -> dict[str, str]:
        return dict(self.SUPPORTED_LANGUAGES)

    def t(self, key: str, **kwargs: Any) -> str:
        return self.translate(key, **kwargs)

    def translate(self, key: str, **kwargs: Any) -> str:
        translated = self._resolve(self.translations.get(self.current_language, {}), key)

        if translated is None:
            translated = self._resolve(self.translations.get("en", {}), key)

        if translated is None:
            return key

        if not isinstance(translated, str):
            return str(translated)

        if kwargs:
            try:
                return translated.format(**kwargs)
            except Exception:
                return translated

        return translated

    def _resolve(self, source: dict, key: str):
        current = source
        for part in key.split("."):
            if not isinstance(current, dict):
                return None
            current = current.get(part)
            if current is None:
                return None
        return current