import os

# Base directory 
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Secret key used for session signing and security on flaskk
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-secret-key'
    
    # SQLite Database URI configuration
    # This automatically creates 'examination_portal.db' in your project root
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'examination_portal.db')
    
    # Disable modification tracking to save resources
    SQLALCHEMY_TRACK_MODIFICATIONS = False