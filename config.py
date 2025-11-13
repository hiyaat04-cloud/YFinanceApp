import os

class Config:
    DEBUG = True

    # Base directory
    basedir = os.path.abspath(os.path.dirname(__file__))

    # Instance folder for the SQLite database
    instance_folder = os.path.join(basedir, 'instance')
    os.makedirs(instance_folder, exist_ok=True)

    # SQLite database path
    DATABASE_PATH = os.path.join(instance_folder, 'finance_app.sqlite3')
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATABASE_PATH}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Security settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'supersecretkey')
    SECURITY_PASSWORD_SALT = 'financeapp_salt'

    # Caching (in-memory for simplicity)
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 30
