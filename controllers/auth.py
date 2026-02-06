"""
Auth controller: login, logout, register.
"""
from flask import Blueprint, request, session, redirect, url_for, render_template, flash
from extensions import db
from models import User, ROLE_ADMIN
from utils.i18n import t as _t
from utils.auth_helpers import username_hash as _username_hash, email_hash as _email_hash
from controllers.decorators import login_required, admin_required

auth_bp = Blueprint('auth', __name__)


def register_allowed():
    if User.query.count() == 0:
        return True
    if 'user_id' not in session:
        return False
    user = User.query.get(session['user_id'])
    return user and user.role == ROLE_ADMIN


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        if not register_allowed():
            if 'user_id' in session:
                flash(_t('msg_only_admins'), 'error')
                return redirect(url_for('pages.products'))
            flash(_t('msg_contact_admin'), 'info')
            return redirect(url_for('auth.login'))
        return render_template('register.html', is_first_user=User.query.count() == 0)
    if request.method == 'POST':
        if not register_allowed():
            flash(_t('msg_only_admins'), 'error')
            return redirect(url_for('auth.login'))
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        if not username or not email or not password:
            flash(_t('msg_all_required'), 'error')
            return render_template('register.html', is_first_user=User.query.count() == 0)
        if password != confirm:
            flash(_t('msg_passwords_dont_match'), 'error')
            return render_template('register.html', is_first_user=User.query.count() == 0)
        if len(password) < 6:
            flash(_t('msg_password_min'), 'error')
            return render_template('register.html', is_first_user=User.query.count() == 0)
        if User.query.filter_by(username_hash=_username_hash(username)).first():
            flash(_t('msg_username_exists'), 'error')
            return render_template('register.html', is_first_user=User.query.count() == 0)
        if User.query.filter_by(email_hash=_email_hash(email)).first():
            flash(_t('msg_email_registered'), 'error')
            return render_template('register.html', is_first_user=User.query.count() == 0)
        user = User()
        user.set_username(username)
        user.set_email(email)
        user.set_password(password)
        user.role = ROLE_ADMIN if User.query.count() == 0 else ROLE_USER
        db.session.add(user)
        db.session.commit()
        is_first = User.query.count() == 1
        flash(_t('msg_registration_success') if is_first else _t('msg_user_created'), 'success')
        return redirect(url_for('auth.login') if is_first else url_for('pages.users_page'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if not username or not password:
            flash(_t('msg_enter_credentials'), 'error')
            return render_template('login.html')
        user = User.query.filter_by(username_hash=_username_hash(username)).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            flash(_t('msg_welcome_back', username=user.username), 'success')
            return redirect(url_for('main.index'))
        flash(_t('msg_invalid_credentials'), 'error')
        return render_template('login.html')
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    session.clear()
    flash(_t('msg_logged_out'), 'info')
    return redirect(url_for('auth.login'))
