"""
Flask extensions (e.g. SQLAlchemy). Initialized in app, imported by models and controllers.
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
