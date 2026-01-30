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
import hashlib
import qrcode
import io
import json
import uuid
from datetime import datetime
import os

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


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username_enc = db.Column(db.LargeBinary, nullable=False)
    username_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email_enc = db.Column(db.LargeBinary, nullable=False)
    email_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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
        except Exception as e:
            app.logger.warning(f"Migration check failed: {e}")

        try:
            db.create_all()
            if Product.query.count() == 0:
                for p in [Product(id='1', name='Latte', price=4.5), Product(id='2', name='Cappuccino', price=5.2), Product(id='3', name='Espresso', price=3.0)]:
                    db.session.add(p)
                db.session.commit()
        except OperationalError as e:
            app.logger.warning(f"Database not available: {e}")
            db.session.rollback()
        except Exception as e:
            db.session.rollback()
            app.logger.warning(f"Default products: {e}")


_db_initialized = False


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
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


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        if not username or not email or not password:
            flash('All fields are required', 'error')
            return render_template('register.html')
        if password != confirm:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
        if len(password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return render_template('register.html')
        if User.query.filter_by(username_hash=_username_hash(username)).first():
            flash('Username already exists', 'error')
            return render_template('register.html')
        if User.query.filter_by(email_hash=_email_hash(email)).first():
            flash('Email already registered', 'error')
            return render_template('register.html')
        user = User()
        user.set_username(username)
        user.set_email(email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if not username or not password:
            flash('Please enter both username and password', 'error')
            return render_template('login.html')
        user = User.query.filter_by(username_hash=_username_hash(username)).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('index'))
        flash('Invalid username or password', 'error')
        return render_template('login.html')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    cart = session.get('cart', [])
    cart_total = sum(item['price'] for item in cart)
    products = [p.to_dict() for p in Product.query.all()]
    return render_template('index.html', products=products, cart=cart, cart_total=cart_total, username=session.get('username'))


@app.route('/api/products', methods=['POST'])
@login_required
def add_product():
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    try:
        price = float(data.get('price', 0))
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid price format'}), 400
    if not name or price <= 0:
        return jsonify({'error': 'Invalid name or price'}), 400
    product = Product(id=str(uuid.uuid4()), name=name, price=round(price, 2), user_id=session.get('user_id'))
    db.session.add(product)
    db.session.commit()
    return jsonify(product.to_dict()), 201


@app.route('/api/products/<product_id>/qr')
@login_required
def get_product_qr(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
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
        return jsonify({'error': 'Invalid price format'}), 400
    if not name or price <= 0:
        return jsonify({'error': 'Invalid name or price'}), 400
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    product.name = name
    product.price = round(price, 2)
    db.session.commit()
    return jsonify(product.to_dict()), 200


@app.route('/api/products/<product_id>', methods=['DELETE'])
@login_required
def delete_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    if product.id in ('1', '2', '3'):
        return jsonify({'error': 'Cannot delete default products'}), 400
    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': 'Product deleted'}), 200


@app.route('/api/products/bulk-delete', methods=['POST'])
@login_required
def bulk_delete_products():
    data = request.get_json() or {}
    product_ids = data.get('product_ids') or []
    if not isinstance(product_ids, list):
        return jsonify({'error': 'Invalid product IDs'}), 400
    product_ids = [p for p in product_ids if p not in ('1', '2', '3')]
    if not product_ids:
        return jsonify({'error': 'No valid products to delete'}), 400
    products = Product.query.filter(Product.id.in_(product_ids)).all()
    for p in products:
        db.session.delete(p)
    db.session.commit()
    return jsonify({'message': f'{len(products)} product(s) deleted', 'deleted_count': len(products)}), 200


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
            return jsonify({'message': 'Added to cart', 'cart': cart}), 200
    if 'name' in data and 'price' in data:
        cart = session.get('cart', [])
        cart.append({
            'id': str(uuid.uuid4()),
            'name': data['name'],
            'price': float(data['price']),
            'product_id': data.get('id'),
        })
        session['cart'] = cart
        return jsonify({'message': 'Added to cart', 'cart': cart}), 200
    return jsonify({'error': 'Invalid data'}), 400


@app.route('/api/cart', methods=['DELETE'])
@login_required
def clear_cart():
    session['cart'] = []
    return jsonify({'message': 'Cart cleared'}), 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
