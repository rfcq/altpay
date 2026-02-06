"""
Application configuration: paths, database URI, config file.
"""
import json
import os

basedir = os.path.abspath(os.path.dirname(__file__))


def get_config_file_path():
    base = '/tmp' if os.environ.get('VERCEL') else basedir
    instance_dir = os.path.join(base, 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    return os.path.join(instance_dir, 'config.json')


def read_config():
    try:
        path = get_config_file_path()
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def write_config(data):
    path = get_config_file_path()
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def get_database_uri():
    raw = (read_config().get('database_url') or '').strip()
    if not raw:
        raw = (os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL') or '').strip()
    if raw and ('postgresql://' in raw or 'postgres://' in raw):
        if raw.startswith('postgres://'):
            raw = raw.replace('postgres://', 'postgresql://', 1)
        return raw
    if os.environ.get('VERCEL'):
        return 'sqlite:////tmp/altpay.db'
    return f'sqlite:///{os.path.join(basedir, "altpay.db")}'


def mask_database_uri(uri):
    """Mask password in URI for display."""
    if not uri or '://' not in uri:
        return uri or ''
    try:
        scheme, rest = uri.split('://', 1)
        if '@' in rest and (scheme == 'postgresql' or scheme == 'postgres'):
            user_part, host_part = rest.rsplit('@', 1)
            if ':' in user_part:
                user, _ = user_part.split(':', 1)
                return f'{scheme}://{user}:****@{host_part}'
        return f'{scheme}://...'
    except Exception:
        return '...'


def is_ephemeral_db():
    """True when on Vercel without a persistent DATABASE_URL."""
    if not os.environ.get('VERCEL'):
        return False
    raw = (os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL') or '').strip()
    return not (raw and ('postgresql://' in raw or 'postgres://' in raw))


def get_discogs_credentials():
    """Return (token, key, secret) from config file, then env. Token or (key+secret) used for API."""
    cfg = read_config()
    token = (cfg.get('discogs_token') or os.environ.get('DISCOGS_TOKEN') or '').strip()
    key = (cfg.get('discogs_consumer_key') or os.environ.get('DISCOGS_CONSUMER_KEY') or '').strip()
    secret = (cfg.get('discogs_consumer_secret') or os.environ.get('DISCOGS_CONSUMER_SECRET') or '').strip()
    return token, key, secret


def is_discogs_configured():
    """True if Discogs can be used (token or key+secret)."""
    token, key, secret = get_discogs_credentials()
    return bool(token or (key and secret))
