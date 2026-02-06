"""
AltPay - Flask app (MVC). Creates app, loads config, registers blueprints.
"""
import os
from flask import Flask

from config import get_database_uri
from extensions import db
from models import User, Product, Sale, SaleItem  # noqa: F401 - register models with db
from controllers.main import main_bp
from controllers.auth import auth_bp
from controllers.pages import pages_bp
from controllers.config_ctrl import config_bp
from controllers.api_products import api_products_bp
from controllers.api_cart import api_cart_bp
from controllers.api_discogs import api_discogs_bp

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = get_database_uri()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(pages_bp)
app.register_blueprint(config_bp)
app.register_blueprint(api_products_bp)
app.register_blueprint(api_cart_bp)
app.register_blueprint(api_discogs_bp)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
