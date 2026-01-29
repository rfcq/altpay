from flask import Flask, render_template, request, jsonify, session, send_file, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from cryptography.fernet import Fernet
from sqlalchemy import inspect, text
import hashlib
import qrcode
import io
import json
import uuid
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "altpay.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

def _instance_key_path() -> str:
    instance_dir = os.path.join(basedir, 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    return os.path.join(instance_dir, 'fernet.key')


def _get_or_create_fernet_key() -> bytes:
    # Prefer env var (useful for production deployments)
    env_key = os.environ.get('APP_ENCRYPTION_KEY')
    if env_key:
        return env_key.encode('utf-8')

    # Dev-friendly: persist key on disk so encrypted data remains readable
    key_path = _instance_key_path()
    if os.path.exists(key_path):
        with open(key_path, 'rb') as f:
            return f.read().strip()

    key = Fernet.generate_key()
    with open(key_path, 'wb') as f:
        f.write(key)
    return key


_FERNET = Fernet(_get_or_create_fernet_key())


def _normalize_username(username: str) -> str:
    return username.strip().lower()


def _username_hash(username: str) -> str:
    # Deterministic hash for lookup + uniqueness; peppered with SECRET_KEY
    pepper = app.secret_key or ''
    normalized = _normalize_username(username)
    return hashlib.sha256(f'{pepper}:{normalized}'.encode('utf-8')).hexdigest()


def _email_hash(email: str) -> str:
    pepper = app.secret_key or ''
    normalized = email.strip().lower()
    return hashlib.sha256(f'{pepper}:{normalized}'.encode('utf-8')).hexdigest()


def _encrypt_str(value: str) -> bytes:
    return _FERNET.encrypt(value.encode('utf-8'))


def _decrypt_str(token: bytes) -> str:
    return _FERNET.decrypt(token).decode('utf-8')


# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Encrypted-at-rest fields + deterministic hashes for lookup/uniqueness
    username_enc = db.Column(db.LargeBinary, nullable=False)
    username_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email_enc = db.Column(db.LargeBinary, nullable=False)
    email_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def username(self) -> str:
        return _decrypt_str(self.username_enc)

    @property
    def email(self) -> str:
        return _decrypt_str(self.email_enc)

    def set_username(self, username: str) -> None:
        self.username_enc = _encrypt_str(username.strip())
        self.username_hash = _username_hash(username)

    def set_email(self, email: str) -> None:
        self.email_enc = _encrypt_str(email.strip())
        self.email_hash = _email_hash(email)

    def set_password(self, password):
        # Passwords should be hashed (one-way), not encrypted (reversible)
        self.password_hash = generate_password_hash(password, method='scrypt')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username_hash}>'


# Product model
class Product(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price
        }


# Create tables
with app.app_context():
    # Lightweight migration from old schema (username/email plaintext) to new encrypted schema
    inspector = inspect(db.engine)
    if 'user' in inspector.get_table_names():
        cols = {c['name'] for c in inspector.get_columns('user')}
        if 'username' in cols and 'username_enc' not in cols:
            with db.engine.begin() as conn:
                # Create a new table with the new schema
                conn.execute(
                    text(
                        """
                        CREATE TABLE IF NOT EXISTS user_new (
                            id INTEGER PRIMARY KEY,
                            username_enc BLOB NOT NULL,
                            username_hash VARCHAR(64) NOT NULL UNIQUE,
                            email_enc BLOB NOT NULL,
                            email_hash VARCHAR(64) NOT NULL UNIQUE,
                            password_hash VARCHAR(255) NOT NULL,
                            created_at DATETIME
                        )
                        """
                    )
                )
                rows = conn.execute(
                    text("SELECT id, username, email, password_hash, created_at FROM user")
                ).fetchall()
                for r in rows:
                    conn.execute(
                        text(
                            """
                            INSERT INTO user_new
                                (id, username_enc, username_hash, email_enc, email_hash, password_hash, created_at)
                            VALUES
                                (:id, :username_enc, :username_hash, :email_enc, :email_hash, :password_hash, :created_at)
                            """
                        ),
                        {
                            'id': r[0],
                            'username_enc': _encrypt_str(r[1]),
                            'username_hash': _username_hash(r[1]),
                            'email_enc': _encrypt_str(r[2]),
                            'email_hash': _email_hash(r[2]),
                            'password_hash': r[3],
                            'created_at': r[4],
                        },
                    )
                conn.execute(text("DROP TABLE user"))
                conn.execute(text("ALTER TABLE user_new RENAME TO user"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_user_username_hash ON user (username_hash)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_user_email_hash ON user (email_hash)"))

    db.create_all()
    # Add default products if they don't exist
    if Product.query.count() == 0:
        default_products = [
            Product(id='1', name='Latte', price=4.5),
            Product(id='2', name='Cappuccino', price=5.2),
            Product(id='3', name='Espresso', price=3.0),
        ]
        for product in default_products:
            db.session.add(product)
        db.session.commit()


# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.before_request
def initialize_session():
    """Initialize cart in session if it doesn't exist"""
    if 'cart' not in session:
        session['cart'] = []


# Auth routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validation
        if not username or not email or not password:
            flash('All fields are required', 'error')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return render_template('register.html')

        # Check if user already exists
        if User.query.filter_by(username_hash=_username_hash(username)).first():
            flash('Username already exists', 'error')
            return render_template('register.html')

        if User.query.filter_by(email_hash=_email_hash(email)).first():
            flash('Email already registered', 'error')
            return render_template('register.html')

        # Create new user
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
        else:
            flash('Invalid username or password', 'error')
            return render_template('login.html')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))


# Main routes
@app.route('/')
@login_required
def index():
    cart = session.get('cart', [])
    cart_total = sum(item['price'] for item in cart)
    all_products = Product.query.all()
    products = [p.to_dict() for p in all_products]
    return render_template('index.html', products=products, cart=cart, cart_total=cart_total, username=session.get('username'))


@app.route('/api/products', methods=['POST'])
@login_required
def add_product():
    data = request.json
    name = data.get('name', '').strip()
    price = data.get('price', 0)
    
    try:
        price = float(price)
        if not name or price <= 0:
            return jsonify({'error': 'Invalid name or price'}), 400
        
        product = Product(
            id=str(uuid.uuid4()),
            name=name,
            price=round(price, 2),
            user_id=session.get('user_id')
        )
        
        db.session.add(product)
        db.session.commit()
        
        return jsonify(product.to_dict()), 201
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid price format'}), 400


@app.route('/api/products/<product_id>/qr')
@login_required
def get_product_qr(product_id):
    product = Product.query.get(product_id)
    
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    # Generate QR code with product data
    qr_data = json.dumps({
        'id': product.id,
        'name': product.name,
        'price': product.price
    })
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    
    return send_file(img_io, mimetype='image/png')


@app.route('/api/cart', methods=['POST'])
@login_required
def add_to_cart():
    data = request.json
    
    # Check if it's a product ID from the list
    product_id = data.get('product_id')
    if product_id:
        product = Product.query.get(product_id)
        if product:
            cart = session.get('cart', [])
            cart.append({
                'id': str(uuid.uuid4()),
                'name': product.name,
                'price': product.price
            })
            session['cart'] = cart
            return jsonify({'message': 'Added to cart', 'cart': cart}), 200
    
    # Check if it's scanned QR data
    if 'name' in data and 'price' in data:
        cart = session.get('cart', [])
        cart.append({
            'id': str(uuid.uuid4()),
            'name': data['name'],
            'price': float(data['price'])
        })
        session['cart'] = cart
        return jsonify({'message': 'Added to cart', 'cart': cart}), 200
    
    return jsonify({'error': 'Invalid data'}), 400


@app.route('/api/cart', methods=['GET'])
@login_required
def get_cart():
    cart = session.get('cart', [])
    cart_total = sum(item['price'] for item in cart)
    return jsonify({'cart': cart, 'total': cart_total})


@app.route('/api/cart', methods=['DELETE'])
@login_required
def clear_cart():
    session['cart'] = []
    return jsonify({'message': 'Cart cleared'}), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
