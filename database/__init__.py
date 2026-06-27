"""Database package for Smart Health Monitor System"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Initialize extensions (these are initialized but not bound to an app yet)
db = SQLAlchemy()
login_manager = LoginManager()

__all__ = [
    'db',
    'login_manager'
]
