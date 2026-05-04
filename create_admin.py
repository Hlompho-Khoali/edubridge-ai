# create_admin.py
from app import app, db
from models import User

with app.app_context():
    # Check if admin exists
    admin = User.query.filter_by(email='admin@edubridge.com').first()
    
    if not admin:
        admin = User(
            email='admin@edubridge.com',
            name='System Admin',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Admin user created successfully!")
        print("Email: admin@edubridge.com")
        print("Password: admin123")
    else:
        # Reset password
        admin.set_password('admin123')
        db.session.commit()
        print("Admin password reset successfully!")
        print("Email: admin@edubridge.com")
        print("Password: admin123")