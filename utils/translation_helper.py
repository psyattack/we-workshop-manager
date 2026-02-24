from typing import Dict, Optional
from deep_translator import GoogleTranslator

class TranslationCache:

    _instance: Optional['TranslationCache'] = None
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, str]] = {}  # {original_text: {lang_code: translated_text}}
    
    @classmethod
    def instance(cls) -> 'TranslationCache':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def get(self, original_text: str, target_lang: str) -> Optional[str]:
        if original_text in self._cache:
            return self._cache[original_text].get(target_lang)
        return None
    
    def set(self, original_text: str, target_lang: str, translated_text: str):
        if original_text not in self._cache:
            self._cache[original_text] = {}
        self._cache[original_text][target_lang] = translated_text
    
    def clear(self):
        self._cache.clear()


class DescriptionTranslator:

    LANG_CODE_MAP = {
        'en': 'en',
        'ru': 'ru',
    }
    
    @classmethod
    def get_google_lang_code(cls, app_lang: str) -> str:
        return cls.LANG_CODE_MAP.get(app_lang, 'en')
    
    @classmethod
    def translate(cls, text: str, target_lang: str) -> Optional[str]:
        if not text or not text.strip():
            return text
            
        cache = TranslationCache.instance()

        cached = cache.get(text, target_lang)
        if cached is not None:
            return cached
        
        try:
            google_lang = cls.get_google_lang_code(target_lang)
            translator = GoogleTranslator(source='auto', target=google_lang)
            translated = translator.translate(text)
            
            if translated:
                cache.set(text, target_lang, translated)
                return translated
                
        except Exception as e:
            print(f"[TranslationHelper] Translation error: {e}")
            
        return None
