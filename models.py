from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    
    # Role: 'admin', 'examiner', 'student'
    role = db.Column(db.String(20), nullable=False)
    
    # Status: 'approved', 'pending', 'deactivated'
    status = db.Column(db.String(20), nullable=False, default='approved')

    def set_password(self, password):
        """Hashes raw password and stores it in password_hash."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifies given password against stored hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'