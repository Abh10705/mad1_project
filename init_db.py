from app import app
from database import db
from models import User

def initialize_database():
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")

        admin = User.query.filter_by(role='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@examportal.com', # obviously its a place holder email
                name='System Administrator',
                role='admin',
                status='approved'
            )
            admin.set_password('admin123')
            
            db.session.add(admin)
            db.session.commit()
            print("Pre-seeded Admin creds.. created successfully!")
            print("Username: admin | Password: admin123")
        else:
            print("Admin superuser already exists.")

if __name__ == '__main__':
    initialize_database()