#!/usr/bin/env python3
"""
Script to create the default admin user for ENABLEDRM
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database.database import SessionLocal, engine
from app.models.user_models import User
from app.core.security import get_password_hash

def create_admin_user():
    """Create the default admin user"""
    db: Session = SessionLocal()
    
    try:
        # Check if admin user already exists
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if existing_admin:
            print("✅ Admin user already exists")
            print(f"   Username: {existing_admin.username}")
            print(f"   Email: {existing_admin.email}")
            print(f"   Role: {existing_admin.role}")
            print(f"   Active: {existing_admin.is_active}")
            return
        
        # Create admin user
        admin_user = User(
            username="admin",
            email="admin@enabledrm.local",
            hashed_password=get_password_hash("admin123"),
            role="administrator",
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("✅ Admin user created successfully!")
        print(f"   Username: admin")
        print(f"   Password: admin123")
        print(f"   Email: admin@enabledrm.local")
        print(f"   Role: administrator")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

def list_all_users():
    """List all users in the database"""
    db: Session = SessionLocal()
    
    try:
        users = db.query(User).all()
        print(f"\n📋 Found {len(users)} users in database:")
        for user in users:
            print(f"   • {user.username} ({user.email}) - {user.role} - {'Active' if user.is_active else 'Inactive'}")
    except Exception as e:
        print(f"❌ Error listing users: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 ENABLEDRM Admin User Setup")
    print("=" * 40)
    
    create_admin_user()
    list_all_users()
    
    print("\n🎉 Setup complete!")
    print("You can now login with:")
    print("   Username: admin")
    print("   Password: admin123")