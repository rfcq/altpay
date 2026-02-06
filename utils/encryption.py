"""
Fernet encryption for usernames/emails. Uses APP_ENCRYPTION_KEY or instance/fernet.key.
"""
import os
from cryptography.fernet import Fernet

from config import basedir


def get_instance_key_path():
    base = '/tmp' if os.environ.get('VERCEL') else basedir
    instance_dir = os.path.join(base, 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    return os.path.join(instance_dir, 'fernet.key')


def get_fernet():
    env_key = os.environ.get('APP_ENCRYPTION_KEY')
    if env_key:
        return Fernet(env_key.encode('utf-8'))
    if os.environ.get('VERCEL'):
        raise RuntimeError('Missing APP_ENCRYPTION_KEY. Set it in Vercel environment variables.')
    key_path = get_instance_key_path()
    if os.path.exists(key_path):
        with open(key_path, 'rb') as f:
            return Fernet(f.read().strip())
    key = Fernet.generate_key()
    with open(key_path, 'wb') as f:
        f.write(key)
    return Fernet(key)


_fernet = None


def _get_fernet():
    global _fernet
    if _fernet is None:
        _fernet = get_fernet()
    return _fernet


def encrypt_str(value):
    return _get_fernet().encrypt(value.encode('utf-8'))


def decrypt_str(token):
    return _get_fernet().decrypt(token).decode('utf-8')
