"""
i18n helpers: current language and translated strings.
"""
from flask import session

from translations import TRANSLATIONS, JS_KEYS


def get_current_lang():
    return session.get('lang') or 'en'


def t(key, **kwargs):
    """Get translated string for current language."""
    lang = get_current_lang()
    s = TRANSLATIONS.get(lang, TRANSLATIONS['en']).get(key, key)
    if kwargs:
        s = s.format(**kwargs)
    return s
