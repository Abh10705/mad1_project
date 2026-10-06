from app import app, db
from models import User

def initialize_database():
    with app.app_context():
        # 1. Create all tables defined in models.py
        db.create_all()
        print("Database tables created successfully!")

        # 2. Check if an Admin user already exists
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            # Create pre-seeded Admin superuser
            admin = User(
                username='admin',
                email='admin@examportal.com',
                name='System Administrator',
                role='admin',
                status='approved'
            )
            # Hash the default admin password
            admin.set_password('admin123')
            
            db.session.add(admin)
            db.session.commit()
            print("Pre-seeded Admin superuser created successfully!")
            print("Username: admin | Password: admin123")
        else:
            print("Admin superuser already exists.")

if __name__ == '__main__':
    initialize_database()