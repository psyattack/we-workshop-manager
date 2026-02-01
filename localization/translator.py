import json
from pathlib import Path
from typing import Dict

class Translator:
    SUPPORTED_LANGUAGES = {
        'en': 'English',
        'ru': 'Русский'
    }
    
    def __init__(self, lang: str = 'en'):
        self.current_lang = lang
        self.translations: Dict[str, dict] = {}
        self._load_translations()
    
    def _load_translations(self):
        localization_dir = Path(__file__).parent
        
        for lang_code in self.SUPPORTED_LANGUAGES.keys():
            lang_file = localization_dir / f"{lang_code}.json"
            if lang_file.exists():
                try:
                    with open(lang_file, 'r', encoding='utf-8') as f:
                        self.translations[lang_code] = json.load(f)
                except Exception as e:
                    print(f"Error loading {lang_code}.json: {e}")
                    self.translations[lang_code] = {}
    
    def set_language(self, lang: str):
        if lang in self.SUPPORTED_LANGUAGES:
            self.current_lang = lang
    
    def get_language(self) -> str:
        return self.current_lang
    
    def translate(self, key: str, **kwargs) -> str:
        keys = key.split('.')
        translation = self.translations.get(self.current_lang, {})
        
        for k in keys:
            if isinstance(translation, dict):
                translation = translation.get(k)
                if translation is None:
                    translation = self.translations.get('en', {})
                    for k2 in keys:
                        if isinstance(translation, dict):
                            translation = translation.get(k2)
                            if translation is None:
                                return key
                    break
            else:
                return key
        
        if translation is None:
            return key
        
        if kwargs and isinstance(translation, str):
            try:
                return translation.format(**kwargs)
            except KeyError:
                return translation
        
        return str(translation)
    
    def t(self, key: str, **kwargs) -> str:
        return self.translate(key, **kwargs)
