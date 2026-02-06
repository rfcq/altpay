"""
Models (M in MVC): User, Product, Sale, SaleItem, init_db.
"""
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError

from extensions import db
from utils.encryption import encrypt_str, decrypt_str
from utils.auth_helpers import username_hash as _username_hash, email_hash as _email_hash

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
        return decrypt_str(self.username_enc)

    @property
    def email(self):
        return decrypt_str(self.email_enc)

    def set_username(self, username):
        self.username_enc = encrypt_str(username.strip())
        self.username_hash = _username_hash(username)

    def set_email(self, email):
        self.email_enc = encrypt_str(email.strip())
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
    grading = db.Column(db.String(100), nullable=True)
    publisher = db.Column(db.String(200), nullable=True)
    year = db.Column(db.Integer, nullable=True)
    cover_path = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    def to_dict(self):
        d = {'id': self.id, 'name': self.name, 'price': self.price}
        if self.grading is not None:
            d['grading'] = self.grading
        if self.publisher is not None:
            d['publisher'] = self.publisher
        if self.year is not None:
            d['year'] = self.year
        if self.cover_path:
            d['cover_path'] = self.cover_path
        return d


class Sale(db.Model):
    __tablename__ = 'sale'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('SaleItem', backref='sale', lazy=True, cascade='all, delete-orphan')


class SaleItem(db.Model):
    __tablename__ = 'sale_item'
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    product_id = db.Column(db.String(36), nullable=True)


def init_db(app):
    """Create tables and run migrations. Call with app context."""
    with app.app_context():
        try:
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
                                'id': r[0], 'ue': encrypt_str(r[1]), 'uh': _username_hash(r[1]),
                                'ee': encrypt_str(r[2]), 'eh': _email_hash(r[2]), 'ph': r[3], 'ca': r[4],
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
                    except Exception:
                        pass
        except Exception as e:
            app.logger.warning(f"Migration check failed: {e}")

        try:
            insp = inspect(db.engine)
            if 'product' in insp.get_table_names():
                pcols = {c['name'] for c in insp.get_columns('product')}
                dialect = db.engine.dialect.name
                ptable = '"product"' if dialect == 'postgresql' else 'product'
                with db.engine.begin() as conn:
                    if 'grading' not in pcols:
                        conn.execute(text(f"ALTER TABLE {ptable} ADD COLUMN grading VARCHAR(100)"))
                    if 'publisher' not in pcols:
                        conn.execute(text(f"ALTER TABLE {ptable} ADD COLUMN publisher VARCHAR(200)"))
                    if 'year' not in pcols:
                        conn.execute(text(f"ALTER TABLE {ptable} ADD COLUMN year INTEGER"))
                    if 'cover_path' not in pcols:
                        conn.execute(text(f"ALTER TABLE {ptable} ADD COLUMN cover_path VARCHAR(500)"))
        except Exception as e:
            app.logger.warning(f"Product migration check failed: {e}")

        try:
            db.create_all()
        except OperationalError as e:
            app.logger.warning(f"Database not available: {e}")
            db.session.rollback()
        except Exception as e:
            db.session.rollback()
            app.logger.warning(f"create_all: {e}")
