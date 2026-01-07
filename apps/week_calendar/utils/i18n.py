"""
Internationalization (i18n) module for multi-language support.

Usage:
    from utils.i18n import t, set_language
    
    # Set language
    set_language('de')
    
    # Get translated string
    title = t('app.title')
"""

import json
from pathlib import Path
from typing import Dict, Optional


class TranslationManager:
    """Manages translations for multiple languages."""
    
    def __init__(self):
        """Initialize translation manager."""
        self.translations: Dict[str, Dict] = {}
        self.current_language = 'de'  # Default: German
        self.translations_dir = Path(__file__).parent.parent / 'translations'
        self._load_all_translations()
    
    def _load_all_translations(self):
        """Load all available translation files."""
        if not self.translations_dir.exists():
            print(f"Translations directory not found: {self.translations_dir}")
            return
        
        for lang_file in self.translations_dir.glob('*.json'):
            lang_code = lang_file.stem
            try:
                with open(lang_file, 'r', encoding='utf-8') as f:
                    self.translations[lang_code] = json.load(f)
                print(f"Loaded translations for: {lang_code}")
            except Exception as e:
                print(f"Error loading {lang_file}: {e}")
    
    def set_language(self, lang_code: str):
        """Set the current language.
        
        Args:
            lang_code: Language code (e.g., 'de', 'en')
        """
        if lang_code in self.translations:
            self.current_language = lang_code
            print(f"Language set to: {lang_code}")
        else:
            print(f"Language '{lang_code}' not available, keeping '{self.current_language}'")
    
    def get(self, key: str, **kwargs) -> str:
        """Get translated string by key.
        
        Args:
            key: Translation key (dot notation, e.g., 'app.title')
            **kwargs: Optional format arguments
            
        Returns:
            Translated string or key if not found
        """
        # Get current language translations
        lang_dict = self.translations.get(self.current_language, {})
        
        # Navigate nested keys
        keys = key.split('.')
        value = lang_dict
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                value = None
                break
        
        # Fallback to English if not found
        if value is None and self.current_language != 'en':
            lang_dict = self.translations.get('en', {})
            value = lang_dict
            for k in keys:
                if isinstance(value, dict):
                    value = value.get(k)
                else:
                    value = None
                    break
        
        # Fallback to key itself
        if value is None:
            return key
        
        # Format with kwargs if provided
        if kwargs and isinstance(value, str):
            try:
                return value.format(**kwargs)
            except KeyError:
                return value
        
        return str(value)
    
    def get_available_languages(self) -> Dict[str, str]:
        """Get available languages with their native names.
        
        Returns:
            Dict mapping language codes to native names
        """
        languages = {}
        for lang_code in self.translations.keys():
            lang_dict = self.translations[lang_code]
            native_name = lang_dict.get('_meta', {}).get('native_name', lang_code)
            languages[lang_code] = native_name
        return languages


# Global instance
_translator = TranslationManager()


def t(key: str, **kwargs) -> str:
    """Get translated string (convenience function).
    
    Args:
        key: Translation key
        **kwargs: Optional format arguments
        
    Returns:
        Translated string
    """
    return _translator.get(key, **kwargs)


def set_language(lang_code: str):
    """Set current language (convenience function).
    
    Args:
        lang_code: Language code
    """
    _translator.set_language(lang_code)


def get_current_language() -> str:
    """Get current language code.
    
    Returns:
        Current language code
    """
    return _translator.current_language


def get_available_languages() -> Dict[str, str]:
    """Get available languages.
    
    Returns:
        Dict mapping language codes to native names
    """
    return _translator.get_available_languages()
