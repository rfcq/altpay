"""
Main controller: index, choose-language, before_request, context_processor.
"""
import json
from flask import Blueprint, request, redirect, url_for, render_template, session
from translations import TRANSLATIONS, SUPPORTED_LANGS, JS_KEYS

from extensions import db
from models import User, init_db
from config import is_ephemeral_db
from utils.i18n import get_current_lang, t as _t
from controllers.decorators import login_required

main_bp = Blueprint('main', __name__)

_db_initialized = False


@main_bp.before_app_request
def before_request_db_and_cart():
    import os
    global _db_initialized
    from flask import current_app
    if not _db_initialized:
        if os.environ.get('VERCEL') and not (os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')):
            _db_initialized = True
        else:
            try:
                init_db(current_app)
            except Exception as e:
                current_app.logger.warning(f"init_db failed: {e}")
            _db_initialized = True
    if 'cart' not in session:
        session['cart'] = []


@main_bp.before_app_request
def ensure_lang():
    if request.endpoint in (None, 'main.choose_language', 'static', 'auth.login', 'auth.register'):
        return
    if session.get('lang') is None:
        return redirect(url_for('main.choose_language', next=request.url))


@main_bp.app_context_processor
def inject_globals():
    lang = get_current_lang()
    strings = TRANSLATIONS.get(lang, TRANSLATIONS['en'])
    js_translations = {k: strings.get(k, TRANSLATIONS['en'].get(k, k)) for k in JS_KEYS}
    out = {
        'use_ephemeral_db': is_ephemeral_db(),
        'strings': strings,
        'current_lang': lang,
        'js_translations': json.dumps(js_translations),
    }
    if 'user_id' in session:
        try:
            user = User.query.get(session['user_id'])
            out['is_admin'] = user.is_admin if user else False
        except Exception:
            out['is_admin'] = False
    else:
        out['is_admin'] = False
    return out


@main_bp.route('/')
@login_required
def index():
    return redirect(url_for('pages.products'))


@main_bp.route('/choose-language')
def choose_language():
    lang = request.args.get('lang')
    next_url = request.args.get('next') or url_for('auth.login')
    if lang in SUPPORTED_LANGS:
        session['lang'] = lang
        return redirect(next_url)
    return render_template('choose_language.html', next_url=next_url or url_for('auth.login'))
