"""
Auth helpers: username/email hashing (peppered with secret_key).
"""
import hashlib
from flask import current_app


def username_hash(username):
    pepper = (current_app.secret_key or '') if current_app else ''
    normalized = (username or '').strip().lower()
    return hashlib.sha256(f'{pepper}:{normalized}'.encode('utf-8')).hexdigest()


def email_hash(email):
    pepper = (current_app.secret_key or '') if current_app else ''
    normalized = (email or '').strip().lower()
    return hashlib.sha256(f'{pepper}:{normalized}'.encode('utf-8')).hexdigest()
