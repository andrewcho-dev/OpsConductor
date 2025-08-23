# Auth Service to User Service Migration

## Overview

This migration refactors the authentication architecture to move user management from the auth service to a dedicated user service, eliminating data duplication and creating a proper separation of concerns.

## Changes Made

### 1. User Service Enhancements

#### Database Schema Changes
- **Added `password_hash` field** to the `users` table for authentication
- **Created migration script**: `services/user-service/database/03_add_password_hash.sql`

#### New Authentication Methods
- `authenticate_user(username, password)` - Full authentication with password verification
- `get_user_for_auth(username)` - Get user data for auth service
- `set_user_password(user_id, password)` - Set/update user password

#### New API Endpoints
- `POST /api/v1/users/authenticate` - Authenticate user credentials
- `GET /api/v1/users/auth/{username}` - Get user data for authentication
- `POST /api/v1/users/{user_id}/password` - Set user password

#### Schema Updates
- Added `password` field to `UserCreateRequest`
- Added `UserAuthenticationRequest` and `UserAuthenticationResponse` schemas

### 2. Auth Service Refactoring

#### Removed In-Memory User Storage
- **Removed `USERS_DB`** dictionary
- **Updated login endpoint** to call user service for authentication
- **Updated user listing** to proxy requests to user service

#### Enhanced Token Creation
- Modified `create_access_token()` to use permissions from user service
- Maintains backward compatibility with role-based permissions as fallback

#### Service Integration
- Added `USER_SERVICE_URL` configuration
- Implemented HTTP client calls to user service using `httpx`
- Added proper error handling for service communication

### 3. Migration Tools

#### Database Migration
- **`services/user-service/database/03_add_password_hash.sql`**
  - Adds password_hash column to users table
  - Creates performance index
  - Adds column documentation

#### User Data Migration
- **`migrate_users_to_user_service.py`**
  - Migrates existing users from auth service to user service
  - Handles duplicate detection
  - Provides migration status reporting

#### Initial Data Seeding
- **`services/user-service/seed_initial_users.py`**
  - Creates initial roles and permissions
  - Seeds default users (admin, user, testuser, operator)
  - Sets up proper role-permission relationships

## Migration Steps

### 1. Apply Database Migration
```bash
# Connect to user service database and run:
psql -h user-postgres -U user_user -d user_db -f services/user-service/database/03_add_password_hash.sql
```

### 2. Seed Initial Data
```bash
cd services/user-service
python seed_initial_users.py
```

### 3. Start Services
```bash
# Start user service first
docker-compose up user-service -d

# Then start auth service
docker-compose up auth-service -d
```

### 4. Verify Migration
```bash
# Test authentication
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Test user listing
curl http://localhost:8000/api/v1/auth/users
```

## Architecture Benefits

### Before (Issues)
- ❌ Duplicate user data in auth service and user service
- ❌ Inconsistent user information across services
- ❌ Auth service managing user data (violates SRP)
- ❌ Hard-coded user credentials in auth service
- ❌ No centralized user management

### After (Improvements)
- ✅ **Single source of truth** for user data in user service
- ✅ **Proper separation of concerns** - auth service handles tokens, user service handles users
- ✅ **Centralized user management** with comprehensive CRUD operations
- ✅ **Database-backed user storage** with proper relationships
- ✅ **Role-based permissions** from database instead of hard-coded mappings
- ✅ **Scalable architecture** ready for additional user-related features

## Service Communication Flow

### Authentication Flow
1. **Frontend** → `POST /api/v1/auth/login` → **Auth Service**
2. **Auth Service** → `POST /api/v1/users/authenticate` → **User Service**
3. **User Service** → Validates credentials → Returns user data
4. **Auth Service** → Creates JWT token → Returns to frontend

### User Management Flow
1. **Frontend** → User management requests → **User Service** (direct)
2. **Auth Service** → User lookup requests → **User Service** (for token validation)

## Configuration

### Environment Variables
```bash
# Auth Service
USER_SERVICE_URL=http://user-service:8000

# User Service  
DATABASE_URL=postgresql://user_user:user_password@user-postgres:5432/user_db
```

## Testing

### Test Authentication
```bash
# Test with admin user
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Test with regular user
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "user123"}'
```

### Test User Management
```bash
# Get user by ID (requires auth token)
curl -H "Authorization: Bearer <token>" \
  http://localhost:8001/api/v1/users/1

# List users (requires auth token)
curl -H "Authorization: Bearer <token>" \
  http://localhost:8001/api/v1/users/
```

## Rollback Plan

If issues arise, you can temporarily rollback by:

1. **Restore USERS_DB** in auth service
2. **Revert login endpoint** to use in-memory authentication
3. **Comment out user service calls**

The rollback code is preserved in git history for reference.

## Future Enhancements

With this architecture in place, we can now easily add:

- **Password reset functionality**
- **Email verification**
- **User profile management**
- **Advanced role hierarchies**
- **User activity logging**
- **OAuth integration**
- **Multi-factor authentication**

## Security Considerations

- ✅ Passwords are properly hashed using bcrypt
- ✅ Service-to-service communication uses internal network
- ✅ JWT tokens contain user permissions for authorization
- ✅ User service validates all user operations
- ✅ Proper error handling prevents information leakage

## Monitoring

Monitor these metrics post-migration:
- **Authentication success/failure rates**
- **Service-to-service communication latency**
- **User service database performance**
- **Token validation performance**

## Support

For issues or questions about this migration:
1. Check service logs: `docker-compose logs auth-service user-service`
2. Verify database connectivity
3. Test service-to-service communication
4. Review configuration environment variables