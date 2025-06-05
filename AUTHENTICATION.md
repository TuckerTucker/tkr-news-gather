# TKR News Gather - Authentication System

This document describes the Supabase-based authentication system implemented to address security vulnerabilities identified in the security audit.

## Overview

The authentication system replaces hardcoded credentials with a proper user management system using Supabase Auth, implementing:

- ✅ **User Registration & Login** - Secure account creation and authentication
- ✅ **JWT Token-based Authentication** - Stateless authentication with proper expiration
- ✅ **Role-based Access Control** - User, Editor, and Admin roles with different permissions
- ✅ **Row Level Security (RLS)** - Database-level access control
- ✅ **Audit Logging** - Complete audit trail of user actions
- ✅ **Password Security** - Secure password hashing with bcrypt

## Security Improvements

### Addressed Critical Issues

| Issue | Status | Solution |
|-------|--------|----------|
| **CRITICAL-001**: Hardcoded credentials | ✅ Fixed | Replaced with Supabase Auth user database |
| **CRITICAL-002**: Database credentials in env vars | ✅ Mitigated | Added proper RLS policies |
| **HIGH-004**: Overly permissive RLS | ✅ Fixed | Authentication-based access control |

### Additional Security Features

- **Consistent auth delays** - Prevents timing attacks
- **Email confirmation** - Requires email verification for new accounts
- **Token refresh** - Secure token renewal mechanism
- **Scope-based permissions** - Fine-grained access control
- **Audit logging** - Complete user action tracking

## User Roles & Permissions

### User Role (`user`)
- **Scopes**: `["read"]`
- **Permissions**: 
  - View news articles and sessions
  - Access public endpoints
  - View own profile

### Editor Role (`editor`) 
- **Scopes**: `["read", "write"]`
- **Permissions**:
  - All user permissions
  - Create and process news content
  - Save articles to database
  - Run AI processing

### Admin Role (`admin`)
- **Scopes**: `["read", "write", "admin"]` 
- **Permissions**:
  - All editor permissions
  - Run full news pipeline
  - Manage users (view all profiles)
  - Access admin-only endpoints
  - View all audit logs

## API Endpoints

### Authentication Endpoints

#### Register User
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "full_name": "John Doe",
  "role": "user"
}
```

#### Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com", 
  "password": "SecurePassword123!"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "..."
}
```

#### Get Current User
```http
GET /auth/me
Authorization: Bearer <access_token>
```

#### Refresh Token
```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "..."
}
```

#### Logout
```http
POST /auth/logout
Authorization: Bearer <access_token>
```

### Protected Endpoints

All API endpoints now require authentication:

- **Public**: Health check endpoints (`/`, `/health`)
- **API Key**: Province endpoints (`/provinces`)
- **JWT Token**: News and processing endpoints
- **Write Scope**: Processing and database operations
- **Admin Role**: Pipeline management

## Database Schema

### User Profiles Table
```sql
CREATE TABLE user_profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  email VARCHAR(255) NOT NULL,
  full_name VARCHAR(255),
  role VARCHAR(50) NOT NULL DEFAULT 'user',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Row Level Security Policies

All tables now have proper RLS policies:

```sql
-- Example: Articles table
CREATE POLICY "Authenticated users can view articles" ON articles
  FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Editors and admins can insert articles" ON articles
  FOR INSERT WITH CHECK (
    EXISTS (
      SELECT 1 FROM user_profiles 
      WHERE user_id = auth.uid() 
      AND role IN ('editor', 'admin')
    )
  );
```

### Audit Logging
```sql
CREATE TABLE user_audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id),
  action VARCHAR(100) NOT NULL,
  table_name VARCHAR(100),
  record_id UUID,
  details JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Setup Instructions

### 1. Database Migration

Run the authentication migration to set up the required tables and policies:

```bash
# Apply the migration in your Supabase dashboard SQL editor
cat database/auth_migration.sql
```

### 2. Environment Configuration

Ensure these environment variables are set:

```env
# Required for authentication
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key

# Optional: Enhanced security
JWT_SECRET_KEY=your-secret-key
API_KEYS=your-api-key1,your-api-key2
```

### 3. Test Authentication

Run the test script to verify everything works:

```bash
python test_auth.py
```

### 4. Create Admin User

After setup, create an admin user through the API:

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@yourcompany.com",
    "password": "SecureAdminPassword123!",
    "full_name": "System Administrator", 
    "role": "admin"
  }'
```

## Usage Examples

### Frontend Integration

```javascript
// Login
const response = await fetch('/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password123'
  })
});

const { access_token } = await response.json();

// Use token for API calls
const newsResponse = await fetch('/news/ontario', {
  headers: {
    'Authorization': `Bearer ${access_token}`
  }
});
```

### API Client Example

```python
import httpx

# Login
auth_response = httpx.post('http://localhost:8000/auth/login', json={
    'email': 'user@example.com',
    'password': 'password123'
})
token = auth_response.json()['access_token']

# Make authenticated request
headers = {'Authorization': f'Bearer {token}'}
news_response = httpx.get('http://localhost:8000/news/ontario', headers=headers)
```

## Security Best Practices

### For Administrators

1. **Use strong passwords** - Minimum 12 characters with mixed case, numbers, symbols
2. **Enable email confirmation** - Require users to verify email addresses
3. **Regular security reviews** - Monitor audit logs for suspicious activity
4. **Rotate API keys** - Change API keys regularly
5. **Monitor failed login attempts** - Watch for brute force attacks

### For Developers

1. **Always use HTTPS** - Never send tokens over HTTP
2. **Store tokens securely** - Use secure storage mechanisms
3. **Handle token expiration** - Implement proper refresh logic
4. **Validate user input** - Use Pydantic models for validation
5. **Log security events** - Implement comprehensive logging

## Monitoring & Maintenance

### Health Checks

The `/health` endpoint now includes authentication service status:

```json
{
  "status": "healthy",
  "components": {
    "api": "healthy",
    "anthropic": "available", 
    "supabase": "available"
  }
}
```

### Audit Log Queries

Monitor user activity with SQL queries:

```sql
-- Recent user activity
SELECT user_id, action, created_at 
FROM user_audit_log 
WHERE created_at > NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC;

-- Failed login attempts
SELECT details->>'email' as email, COUNT(*) as attempts
FROM user_audit_log 
WHERE action = 'login_failed' 
  AND created_at > NOW() - INTERVAL '1 hour'
GROUP BY details->>'email'
HAVING COUNT(*) > 5;
```

## Troubleshooting

### Common Issues

**Q: "Authentication service unavailable"**
- Check SUPABASE_URL and SUPABASE_ANON_KEY environment variables
- Verify Supabase project is active
- Check network connectivity

**Q: "Invalid or expired token"**
- Token may have expired (default 1 hour)
- Use refresh token to get new access token
- Re-authenticate if refresh token is expired

**Q: "Insufficient permissions"**
- Check user role and scopes
- Verify endpoint requires correct permission level
- Contact admin to update user role if needed

**Q: Database RLS denies access**
- Ensure user is authenticated
- Check if user has required role for operation
- Verify RLS policies are correctly applied

### Support

For issues with the authentication system:

1. Check the test script output: `python test_auth.py`
2. Review application logs for error details
3. Verify database migration was applied correctly
4. Check Supabase dashboard for user and auth status