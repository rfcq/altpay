"""
Config controller: database URL, Discogs integration, erase all users.
"""
from flask import Blueprint, request, session, redirect, url_for, flash, render_template
from extensions import db
from models import User, Product, Sale, SaleItem
from config import read_config, write_config, get_database_uri, mask_database_uri, get_discogs_credentials, is_discogs_configured
from utils.i18n import t as _t
from controllers.decorators import login_required, admin_required

config_bp = Blueprint('config', __name__)


@config_bp.route('/config', methods=['GET', 'POST'])
@login_required
@admin_required
def config_page():
    from flask import current_app
    current_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI') or ''
    masked_uri = mask_database_uri(current_uri)
    config_data = read_config()
    saved_url = (config_data.get('database_url') or '').strip()

    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        form = data if data else request.form

        if form.get('section') == 'discogs':
            config_data = read_config()
            token_val = (form.get('discogs_token') or '').strip()
            key_val = (form.get('discogs_consumer_key') or '').strip()
            secret_val = (form.get('discogs_consumer_secret') or '').strip()
            if token_val:
                config_data['discogs_token'] = token_val
            if key_val:
                config_data['discogs_consumer_key'] = key_val
            if secret_val:
                config_data['discogs_consumer_secret'] = secret_val
            write_config(config_data)
            flash(_t('config_discogs_saved'), 'success')
            return redirect(url_for('config.config_page'))

        url = (data.get('database_url') or request.form.get('database_url') or '').strip()
        if not url:
            config_data = read_config()
            config_data.pop('database_url', None)
            write_config(config_data)
            flash(_t('config_saved_default'), 'success')
            return redirect(url_for('config.config_page'))
        if url.startswith('postgres://'):
            url = url.replace('postgres://', 'postgresql://', 1)
        if not ('postgresql://' in url or 'sqlite://' in url):
            flash(_t('config_invalid_uri'), 'error')
            return redirect(url_for('config.config_page'))
        config_data = read_config()
        config_data['database_url'] = url
        write_config(config_data)
        flash(_t('config_saved_restart'), 'success')
        return redirect(url_for('config.config_page'))

    safe_saved_url = ''
    if saved_url and saved_url.startswith('sqlite://'):
        safe_saved_url = saved_url
    token, key, _ = get_discogs_credentials()
    discogs_token_placeholder = '••••••' if token else ''
    discogs_key_placeholder = (key[:4] + '••••') if key and len(key) >= 4 else ('••••••' if key else '')
    return render_template(
        'config.html',
        username=session.get('username'),
        current_uri_masked=masked_uri,
        saved_database_url=safe_saved_url,
        discogs_configured=is_discogs_configured(),
        discogs_token_placeholder=discogs_token_placeholder,
        discogs_key_placeholder=discogs_key_placeholder,
    )


@config_bp.route('/config/erase-users', methods=['POST'])
@login_required
@admin_required
def config_erase_users():
    confirm = (request.form.get('confirm_erase') or (request.get_json(silent=True) or {}).get('confirm_erase') or '').strip()
    if confirm != 'DELETE ALL':
        flash(_t('config_erase_confirm_required'), 'error')
        return redirect(url_for('config.config_page'))
    try:
        SaleItem.query.delete()
        Sale.query.delete()
        Product.query.delete()
        User.query.delete()
        db.session.commit()
    except Exception as e:
        from flask import current_app
        db.session.rollback()
        current_app.logger.exception(e)
        flash(_t('config_erase_error') + ' ' + str(e), 'error')
        return redirect(url_for('config.config_page'))
    session.clear()
    flash(_t('config_erase_done'), 'success')
    return redirect(url_for('auth.login'))
