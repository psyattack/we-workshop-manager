from typing import Optional

from deep_translator import GoogleTranslator


class TranslationCache:
    _instance: Optional["TranslationCache"] = None

    def __init__(self):
        self._cache: dict[str, dict[str, str]] = {}

    @classmethod
    def instance(cls) -> "TranslationCache":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get(self, original_text: str, target_lang: str) -> Optional[str]:
        if original_text in self._cache:
            return self._cache[original_text].get(target_lang)
        return None

    def set(self, original_text: str, target_lang: str, translated_text: str) -> None:
        if original_text not in self._cache:
            self._cache[original_text] = {}
        self._cache[original_text][target_lang] = translated_text

    def clear(self) -> None:
        self._cache.clear()


class DescriptionTranslationService:
    LANGUAGE_MAP = {
        "en": "en",
        "ru": "ru",
        "de": "de",
        "es": "es",
        "fr": "fr",
        "pt": "pt",
        "ja": "ja",
        "zh": "zh-CN",
    }

    @classmethod
    def get_google_language_code(cls, app_language: str) -> str:
        return cls.LANGUAGE_MAP.get(app_language, "en")

    @classmethod
    def translate(cls, text: str, target_lang: str) -> Optional[str]:
        if not text or not text.strip():
            return text

        cache = TranslationCache.instance()
        cached = cache.get(text, target_lang)
        if cached is not None:
            return cached

        try:
            google_language = cls.get_google_language_code(target_lang)
            translator = GoogleTranslator(source="auto", target=google_language)
            translated = translator.translate(text)

            if translated:
                cache.set(text, target_lang, translated)

            return translated
        except Exception:
            return None