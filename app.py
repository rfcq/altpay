"""
AltPay - Flask app with auth, products, QR codes, and shopping cart.
"""
from flask import Flask, render_template, request, jsonify, session, send_file, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from cryptography.fernet import Fernet
from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError
import csv
import hashlib
import qrcode
import io
import json
import uuid
from datetime import datetime
import os

from translations import TRANSLATIONS, SUPPORTED_LANGS, JS_KEYS

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

basedir = os.path.abspath(os.path.dirname(__file__))


def _get_database_uri():
    raw = (os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL') or '').strip()
    if raw and ('postgresql://' in raw or 'postgres://' in raw):
        if raw.startswith('postgres://'):
            raw = raw.replace('postgres://', 'postgresql://', 1)
        return raw
    if os.environ.get('VERCEL'):
        return 'sqlite:////tmp/altpay.db'
    return f'sqlite:///{os.path.join(basedir, "altpay.db")}'


app.config['SQLALCHEMY_DATABASE_URI'] = _get_database_uri()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


def _is_ephemeral_db():
    """True when on Vercel without a persistent DATABASE_URL (SQLite in /tmp)."""
    if not os.environ.get('VERCEL'):
        return False
    raw = (os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL') or '').strip()
    return not (raw and ('postgresql://' in raw or 'postgres://' in raw))


def get_current_lang():
    return session.get('lang') or 'en'


def _t(key, **kwargs):
    """Get translated string for current language."""
    lang = get_current_lang()
    s = TRANSLATIONS.get(lang, TRANSLATIONS['en']).get(key, key)
    if kwargs:
        s = s.format(**kwargs)
    return s


@app.context_processor
def inject_ephemeral_db_warning():
    lang = get_current_lang()
    strings = TRANSLATIONS.get(lang, TRANSLATIONS['en'])
    js_translations = {k: strings.get(k, TRANSLATIONS['en'].get(k, k)) for k in JS_KEYS}
    out = {
        'use_ephemeral_db': _is_ephemeral_db(),
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


def _instance_key_path():
    base = '/tmp' if os.environ.get('VERCEL') else basedir
    instance_dir = os.path.join(base, 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    return os.path.join(instance_dir, 'fernet.key')


def _get_or_create_fernet_key():
    env_key = os.environ.get('APP_ENCRYPTION_KEY')
    if env_key:
        return env_key.encode('utf-8')
    if os.environ.get('VERCEL'):
        raise RuntimeError('Missing APP_ENCRYPTION_KEY. Set it in Vercel environment variables.')
    key_path = _instance_key_path()
    if os.path.exists(key_path):
        with open(key_path, 'rb') as f:
            return f.read().strip()
    key = Fernet.generate_key()
    with open(key_path, 'wb') as f:
        f.write(key)
    return key


_FERNET = Fernet(_get_or_create_fernet_key())


def _username_hash(username):
    pepper = app.secret_key or ''
    normalized = username.strip().lower()
    return hashlib.sha256(f'{pepper}:{normalized}'.encode('utf-8')).hexdigest()


def _email_hash(email):
    pepper = app.secret_key or ''
    normalized = email.strip().lower()
    return hashlib.sha256(f'{pepper}:{normalized}'.encode('utf-8')).hexdigest()


def _encrypt_str(value):
    return _FERNET.encrypt(value.encode('utf-8'))


def _decrypt_str(token):
    return _FERNET.decrypt(token).decode('utf-8')


ROLE_USER = 'user'
ROLE_ADMIN = 'admin'


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username_enc = db.Column(db.LargeBinary, nullable=False)
    username_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email_enc = db.Column(db.LargeBinary, nullable=False)
    email_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=ROLE_USER)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def is_admin(self):
        return self.role == ROLE_ADMIN

    @property
    def username(self):
        return _decrypt_str(self.username_enc)

    @property
    def email(self):
        return _decrypt_str(self.email_enc)

    def set_username(self, username):
        self.username_enc = _encrypt_str(username.strip())
        self.username_hash = _username_hash(username)

    def set_email(self, email):
        self.email_enc = _encrypt_str(email.strip())
        self.email_hash = _email_hash(email)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='scrypt')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'price': self.price}


def init_db():
    with app.app_context():
        try:
            # Avoid connecting on Vercel when no DATABASE_URL (SQLite would fail)
            if os.environ.get('VERCEL') and not (os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')):
                return
            inspector = inspect(db.engine)
            if 'user' in inspector.get_table_names():
                cols = {c['name'] for c in inspector.get_columns('user')}
                if 'username' in cols and 'username_enc' not in cols:
                    with db.engine.begin() as conn:
                        conn.execute(text("""
                            CREATE TABLE IF NOT EXISTS user_new (
                                id INTEGER PRIMARY KEY,
                                username_enc BLOB NOT NULL,
                                username_hash VARCHAR(64) NOT NULL UNIQUE,
                                email_enc BLOB NOT NULL,
                                email_hash VARCHAR(64) NOT NULL UNIQUE,
                                password_hash VARCHAR(255) NOT NULL,
                                created_at DATETIME
                            )
                        """))
                        rows = conn.execute(text(
                            "SELECT id, username, email, password_hash, created_at FROM user"
                        )).fetchall()
                        for r in rows:
                            conn.execute(text("""
                                INSERT INTO user_new (id, username_enc, username_hash, email_enc, email_hash, password_hash, created_at)
                                VALUES (:id, :ue, :uh, :ee, :eh, :ph, :ca)
                            """), {
                                'id': r[0], 'ue': _encrypt_str(r[1]), 'uh': _username_hash(r[1]),
                                'ee': _encrypt_str(r[2]), 'eh': _email_hash(r[2]), 'ph': r[3], 'ca': r[4],
                            })
                        conn.execute(text("DROP TABLE user"))
                        conn.execute(text("ALTER TABLE user_new RENAME TO user"))
                        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_user_username_hash ON user (username_hash)"))
                        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_user_email_hash ON user (email_hash)"))
            if 'role' not in cols:
                try:
                    dialect = db.engine.dialect.name
                    table = '"user"' if dialect == 'postgresql' else 'user'
                    with db.engine.begin() as conn:
                        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN role VARCHAR(20) DEFAULT 'user' NOT NULL"))
                except Exception as alter_err:
                    app.logger.warning(f"Role column migration: {alter_err}")
        except Exception as e:
            app.logger.warning(f"Migration check failed: {e}")

        try:
            db.create_all()
        except OperationalError as e:
            app.logger.warning(f"Database not available: {e}")
            db.session.rollback()
        except Exception as e:
            db.session.rollback()
            app.logger.warning(f"create_all: {e}")


_db_initialized = False


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        try:
            user = User.query.get(session['user_id'])
            if not user or user.role != ROLE_ADMIN:
                flash(_t('msg_admin_required'), 'error')
                return redirect(url_for('products'))
        except Exception:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.before_request
def before_request():
    global _db_initialized
    if not _db_initialized:
        # On Vercel, skip DB init if no DATABASE_URL (SQLite can't be used; would fail at connect)
        if os.environ.get('VERCEL') and not (os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')):
            _db_initialized = True
        else:
            try:
                init_db()
            except Exception as e:
                app.logger.warning(f"init_db failed: {e}")
                _db_initialized = True  # avoid retrying on every request
            else:
                _db_initialized = True
    if 'cart' not in session:
        session['cart'] = []


@app.before_request
def ensure_lang():
    """Redirect to language selection on first access (no lang in session)."""
    if request.endpoint in (None, 'choose_language', 'static'):
        return
    if session.get('lang') is None:
        next_url = request.url
        return redirect(url_for('choose_language', next=next_url))


@app.route('/choose-language')
def choose_language():
    lang = request.args.get('lang')
    next_url = request.args.get('next') or url_for('login')
    if lang in SUPPORTED_LANGS:
        session['lang'] = lang
        return redirect(next_url)
    return render_template('choose_language.html', next_url=next_url or url_for('login'))


def _register_allowed():
    """Allow register if no users exist (bootstrap first admin) or current user is admin."""
    if User.query.count() == 0:
        return True
    if 'user_id' not in session:
        return False
    user = User.query.get(session['user_id'])
    return user and user.role == ROLE_ADMIN


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        if not _register_allowed():
            if 'user_id' in session:
                flash(_t('msg_only_admins'), 'error')
                return redirect(url_for('products'))
            flash(_t('msg_contact_admin'), 'info')
            return redirect(url_for('login'))
        return render_template('register.html', is_first_user=User.query.count() == 0)
    if request.method == 'POST':
        if not _register_allowed():
            flash(_t('msg_only_admins'), 'error')
            return redirect(url_for('login'))
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
        return redirect(url_for('login') if is_first else url_for('users_page'))


@app.route('/login', methods=['GET', 'POST'])
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
            return redirect(url_for('index'))
        flash(_t('msg_invalid_credentials'), 'error')
        return render_template('login.html')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash(_t('msg_logged_out'), 'info')
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    return redirect(url_for('products'))


@app.route('/create')
@login_required
def create_product_page():
    return render_template('create_product.html', username=session.get('username'))


@app.route('/products')
@login_required
def products():
    products_list = [p.to_dict() for p in Product.query.all()]
    return render_template('products.html', products=products_list, username=session.get('username'))


@app.route('/cart')
@login_required
def cart_page():
    cart = session.get('cart', [])
    cart_total = sum(item['price'] for item in cart)
    return render_template('cart.html', cart=cart, cart_total=cart_total, username=session.get('username'))


@app.route('/users')
@login_required
@admin_required
def users_page():
    users_list = User.query.order_by(User.created_at.desc()).all()
    users_data = [{'id': u.id, 'username': u.username, 'role': u.role, 'created_at': u.created_at} for u in users_list]
    return render_template('users.html', users=users_data, username=session.get('username'))


@app.route('/api/products', methods=['POST'])
@login_required
def add_product():
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    try:
        price = float(data.get('price', 0))
    except (TypeError, ValueError):
        return jsonify({'error': _t('err_invalid_price')}), 400
    if not name or price <= 0:
        return jsonify({'error': _t('err_invalid_name_price')}), 400
    product = Product(id=str(uuid.uuid4()), name=name, price=round(price, 2), user_id=session.get('user_id'))
    db.session.add(product)
    db.session.commit()
    return jsonify(product.to_dict()), 201


def _parse_import_row(row):
    """Normalize a dict row to name/price. Accepts name, nome, price, preco (case-insensitive)."""
    key_map = {k.lower().strip(): k for k in row}
    name_key = next((key_map[k] for k in ('name', 'nome', 'product', 'produto') if k in key_map), None)
    price_key = next((key_map[k] for k in ('price', 'preco', 'preço') if k in key_map), None)
    if not name_key or not price_key:
        return None, None
    name = (row.get(name_key) or '').strip()
    if not name:
        return None, None
    try:
        price = float(str(row.get(price_key) or '0').replace(',', '.').strip())
    except (TypeError, ValueError):
        return name, None
    if price <= 0:
        return name, None
    return name, round(price, 2)


@app.route('/api/products/import', methods=['POST'])
@login_required
def import_products():
    if 'file' not in request.files:
        return jsonify({'error': _t('import_no_file')}), 400
    f = request.files['file']
    if not f.filename:
        return jsonify({'error': _t('import_no_file')}), 400
    fn = (f.filename or '').lower()
    if not (fn.endswith('.csv') or fn.endswith('.json')):
        return jsonify({'error': _t('import_bad_type')}), 400
    try:
        content = f.read()
        if isinstance(content, bytes):
            content = content.decode('utf-8', errors='replace')
        created = 0
        errors = []
        user_id = session.get('user_id')
        if fn.endswith('.csv'):
            reader = csv.DictReader(io.StringIO(content), delimiter=',')
            if not reader.fieldnames:
                return jsonify({'error': _t('import_empty')}), 400
            for i, row in enumerate(reader):
                name, price = _parse_import_row(row)
                if name is None and price is None:
                    continue
                if price is None:
                    errors.append(_t('import_row_invalid', row=i + 2))
                    continue
                db.session.add(Product(id=str(uuid.uuid4()), name=name, price=price, user_id=user_id))
                created += 1
        else:
            data = json.loads(content)
            if isinstance(data, dict) and 'products' in data:
                items = data['products']
            elif isinstance(data, list):
                items = data
            else:
                return jsonify({'error': _t('import_json_format')}), 400
            for i, item in enumerate(items):
                if not isinstance(item, dict):
                    errors.append(_t('import_row_invalid', row=i + 1))
                    continue
                name, price = _parse_import_row(item)
                if name is None and price is None:
                    continue
                if price is None:
                    errors.append(_t('import_row_invalid', row=i + 1))
                    continue
                db.session.add(Product(id=str(uuid.uuid4()), name=name, price=price, user_id=user_id))
                created += 1
        db.session.commit()
        return jsonify({
            'message': _t('import_success', count=created),
            'created': created,
            'errors': errors[:20],
        }), 200
    except json.JSONDecodeError as e:
        return jsonify({'error': _t('import_json_invalid') + ' ' + str(e)}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.exception(e)
        return jsonify({'error': _t('import_error') + ' ' + str(e)}), 500


@app.route('/api/products/<product_id>/qr')
@login_required
def get_product_qr(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': _t('err_product_not_found')}), 404
    qr_data = json.dumps({'id': product.id, 'name': product.name, 'price': product.price})
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')


@app.route('/api/products/<product_id>', methods=['PUT'])
@login_required
def update_product(product_id):
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    try:
        price = float(data.get('price', 0))
    except (TypeError, ValueError):
        return jsonify({'error': _t('err_invalid_price')}), 400
    if not name or price <= 0:
        return jsonify({'error': _t('err_invalid_name_price')}), 400
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': _t('err_product_not_found')}), 404
    product.name = name
    product.price = round(price, 2)
    db.session.commit()
    return jsonify(product.to_dict()), 200


@app.route('/api/products/<product_id>', methods=['DELETE'])
@login_required
def delete_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': _t('err_product_not_found')}), 404
    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': _t('msg_product_deleted')}), 200


@app.route('/api/products/bulk-delete', methods=['POST'])
@login_required
def bulk_delete_products():
    data = request.get_json() or {}
    product_ids = data.get('product_ids') or []
    if not isinstance(product_ids, list):
        return jsonify({'error': _t('err_invalid_product_ids')}), 400
    if not product_ids:
        return jsonify({'error': _t('err_no_valid_products')}), 400
    products = Product.query.filter(Product.id.in_(product_ids)).all()
    for p in products:
        db.session.delete(p)
    db.session.commit()
    n = len(products)
    msg = _t('msg_one_product_deleted') if n == 1 else _t('msg_products_deleted', n=n)
    return jsonify({'message': msg, 'deleted_count': n}), 200


@app.route('/api/cart', methods=['GET'])
@login_required
def get_cart():
    cart = session.get('cart', [])
    total = sum(item['price'] for item in cart)
    return jsonify({'cart': cart, 'total': total})


@app.route('/api/cart', methods=['POST'])
@login_required
def add_to_cart():
    data = request.get_json() or {}
    product_id = data.get('product_id')
    if product_id:
        product = Product.query.get(product_id)
        if product:
            cart = session.get('cart', [])
            cart.append({'id': str(uuid.uuid4()), 'name': product.name, 'price': product.price, 'product_id': product.id})
            session['cart'] = cart
            return jsonify({'message': _t('msg_added_to_cart'), 'cart': cart}), 200
    if 'name' in data and 'price' in data:
        cart = session.get('cart', [])
        cart.append({
            'id': str(uuid.uuid4()),
            'name': data['name'],
            'price': float(data['price']),
            'product_id': data.get('id'),
        })
        session['cart'] = cart
        return jsonify({'message': _t('msg_added_to_cart'), 'cart': cart}), 200
    return jsonify({'error': _t('err_invalid_data')}), 400


@app.route('/api/cart', methods=['DELETE'])
@login_required
def clear_cart():
    session['cart'] = []
    return jsonify({'message': _t('msg_cart_cleared')}), 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
