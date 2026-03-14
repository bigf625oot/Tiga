import gettext
from pathlib import Path
from typing import Optional

from app.core.config import settings

# Global translation object
_translation: Optional[gettext.NullTranslations] = None

def setup_i18n():
    """
    Initialize i18n configuration.
    """
    global _translation
    
    # Path to locales directory
    # backend/app/core/i18n.py -> backend/app/locales
    base_dir = Path(__file__).resolve().parent.parent
    locales_dir = base_dir / "locales"
    
    lang = settings.LANGUAGE
    # Normalize language code (e.g., zh-CN -> zh_CN)
    lang = lang.replace("-", "_")
    
    try:
        # Load translation based on configured language
        # This looks for locales_dir/{lang}/LC_MESSAGES/messages.mo
        # fallback=True ensures that if .mo file is missing, it returns NullTranslations
        # which returns the key as is.
        _translation = gettext.translation(
            domain="messages",
            localedir=str(locales_dir),
            languages=[lang],
            fallback=True
        )
    except Exception as e:
        # Fallback to NullTranslations if loading fails (should be covered by fallback=True, but just in case)
        print(f"Warning: Failed to load translations for language '{lang}': {e}")
        _translation = gettext.NullTranslations()

def get_text(message: str) -> str:
    """
    Translate a message.
    """
    if _translation is None:
        setup_i18n()
    return _translation.gettext(message)

# Alias for get_text, standard in Python i18n
_ = get_text
