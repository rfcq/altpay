"""
Auth decorators: login_required, admin_required.
"""
from functools import wraps
from flask import session, redirect, url_for, flash

from models import User, ROLE_ADMIN
from utils.i18n import t as _t


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        try:
            user = User.query.get(session['user_id'])
            if not user or user.role != ROLE_ADMIN:
                flash(_t('msg_admin_required'), 'error')
                return redirect(url_for('pages.products'))
        except Exception:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function
