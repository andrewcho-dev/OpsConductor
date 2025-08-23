#!/usr/bin/env python3
"""
Migration script to move users from auth service in-memory DB to user service database
"""

import asyncio
import httpx
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Auth service in-memory users (copy from auth service)
USERS_TO_MIGRATE = {
    "admin": {
        "id": 1,
        "username": "admin",
        "email": "admin@opsconductor.local",
        "password_hash": "$2b$12$LQv3c1yqBwWFcDDrHrwine.87M7diNT.jRG4hGAHN7wx/iuBzby1u",  # secret123
        "role": "admin",
        "is_active": True,
        "first_name": "System",
        "last_name": "Administrator"
    },
    "user1": {
        "id": 2,
        "username": "user1",
        "email": "user1@opsconductor.local", 
        "password_hash": "$2b$12$LQv3c1yqBwWFcDDrHrwine.87M7diNT.jRG4hGAHN7wx/iuBzby1u",  # secret123
        "role": "user",
        "is_active": True,
        "first_name": "Test",
        "last_name": "User"
    },
    "operator1": {
        "id": 3,
        "username": "operator1",
        "email": "operator1@opsconductor.local",
        "password_hash": "$2b$12$LQv3c1yqBwWFcDDrHrwine.87M7diNT.jRG4hGAHN7wx/iuBzby1u",  # secret123
        "role": "operator",
        "is_active": True,
        "first_name": "System",
        "last_name": "Operator"
    }
}

USER_SERVICE_URL = "http://localhost:8001"  # Adjust port as needed

async def create_user_in_service(user_data: Dict[str, Any]) -> bool:
    """Create user in user service"""
    try:
        # First check if user already exists
        async with httpx.AsyncClient() as client:
            # Check by email
            try:
                response = await client.get(
                    f"{USER_SERVICE_URL}/api/v1/users/by-email/{user_data['email']}",
                    headers={"Authorization": "Bearer admin-migration-token"},  # You'll need to handle auth
                    timeout=10.0
                )
                if response.status_code == 200:
                    logger.info(f"User {user_data['email']} already exists, skipping")
                    return True
            except:
                pass  # User doesn't exist, continue with creation
            
            # Create user
            create_data = {
                "email": user_data["email"],
                "username": user_data["username"],
                "password": "secret123",  # Will be hashed by user service
                "first_name": user_data.get("first_name"),
                "last_name": user_data.get("last_name"),
                "role_ids": [1] if user_data["role"] == "admin" else [2],  # Assuming role IDs
                "send_welcome_email": False
            }
            
            response = await client.post(
                f"{USER_SERVICE_URL}/api/v1/users/",
                json=create_data,
                headers={"Authorization": "Bearer admin-migration-token"},
                timeout=10.0
            )
            
            if response.status_code == 201:
                logger.info(f"Successfully created user: {user_data['username']}")
                return True
            else:
                logger.error(f"Failed to create user {user_data['username']}: {response.status_code} - {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"Error creating user {user_data['username']}: {e}")
        return False

async def migrate_users():
    """Migrate all users to user service"""
    logger.info("Starting user migration...")
    
    success_count = 0
    total_count = len(USERS_TO_MIGRATE)
    
    for username, user_data in USERS_TO_MIGRATE.items():
        logger.info(f"Migrating user: {username}")
        
        if await create_user_in_service(user_data):
            success_count += 1
        
        # Small delay between requests
        await asyncio.sleep(0.5)
    
    logger.info(f"Migration completed: {success_count}/{total_count} users migrated successfully")

if __name__ == "__main__":
    print("User Migration Script")
    print("====================")
    print("This script will migrate users from auth service to user service.")
    print("Make sure both services are running before proceeding.")
    print()
    
    confirm = input("Do you want to proceed? (y/N): ")
    if confirm.lower() != 'y':
        print("Migration cancelled.")
        exit(0)
    
    asyncio.run(migrate_users())