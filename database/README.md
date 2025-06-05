# Database Schema Files

This directory contains different SQL schema files for setting up the TKR News Gather database. Choose the appropriate file based on your situation.

## Schema Files Overview

### 📄 `schema.sql` (Original)
- **Purpose**: Basic news collection tables only
- **Includes**: News sessions, articles, processed articles, audio files
- **Security**: Public read access (insecure)
- **Use Case**: Legacy installations, development testing

### 📄 `auth_migration.sql` (Migration)
- **Purpose**: Adds authentication to existing `schema.sql` setup
- **Includes**: User profiles, audit logging, RLS policies, auth functions
- **Security**: Full authentication and role-based access control
- **Use Case**: Upgrading existing projects to add security

### 📄 `schema_with_auth.sql` (Complete) ⭐ **RECOMMENDED**
- **Purpose**: Complete schema with news tables + authentication
- **Includes**: Everything from both files above, properly integrated
- **Security**: Full authentication system from the start
- **Use Case**: New projects, fresh installations

## Decision Matrix

| Scenario | Recommended File | Reason |
|----------|------------------|---------|
| **New project** | `schema_with_auth.sql` | Complete setup with security |
| **Existing project with basic schema** | `auth_migration.sql` | Adds security to existing setup |
| **Development/testing only** | `schema.sql` | Simpler setup for testing |
| **Security is required** | `schema_with_auth.sql` | Built-in authentication |

## Security Comparison

| Feature | schema.sql | auth_migration.sql | schema_with_auth.sql |
|---------|------------|-------------------|---------------------|
| User Management | ❌ None | ✅ Full Supabase Auth | ✅ Full Supabase Auth |
| Access Control | ❌ Public access | ✅ Role-based (user/editor/admin) | ✅ Role-based (user/editor/admin) |
| Audit Logging | ❌ None | ✅ Complete audit trail | ✅ Complete audit trail |
| RLS Policies | ❌ Permissive | ✅ Authentication required | ✅ Authentication required |
| Data Protection | ❌ No protection | ✅ Protected by auth | ✅ Protected by auth |

## Setup Instructions

### For New Projects (Recommended)

1. **Use `schema_with_auth.sql`**
2. Create Supabase project
3. Copy-paste entire file into SQL editor
4. Run the schema
5. Configure environment variables
6. Start using authenticated API

### For Existing Projects

1. **Use `auth_migration.sql`**
2. Ensure you have existing tables from `schema.sql`
3. Backup your data first
4. Copy-paste migration file into SQL editor
5. Run the migration
6. Update environment variables
7. Update API calls to use authentication

## Environment Variables Required

After setting up authentication (either method):

```bash
# Required
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key

# Recommended
JWT_SECRET_KEY=your-secret-key
API_KEYS=key1,key2
```

## Schema Relationship

```
schema.sql (Basic)
    ↓
    + auth_migration.sql
    ↓
    = schema_with_auth.sql (Complete)
```

## Migration Path

If you're currently using `schema.sql`:

1. **Export your existing data** (if any)
2. **Apply `auth_migration.sql`** to add authentication
3. **Test authentication** with test users
4. **Update your application** to use new auth endpoints
5. **Create admin users** via API

## Testing Your Setup

After applying any schema:

```bash
# Test the schema setup
python test_auth.py

# Check database connectivity
python -c "from src.utils.supabase_client import SupabaseClient; from src.utils.config import Config; print('✅ Connected' if SupabaseClient(Config()).is_available() else '❌ Failed')"
```

## Security Features Added

The authentication system adds:

- ✅ **User registration and login**
- ✅ **JWT token-based authentication**  
- ✅ **Role-based access control** (user/editor/admin)
- ✅ **Row Level Security policies**
- ✅ **Audit logging** for all user actions
- ✅ **Secure password hashing**
- ✅ **Email confirmation workflow**
- ✅ **Token refresh mechanism**

## Support

- See `AUTHENTICATION.md` for detailed authentication documentation
- Run `python test_auth.py` to validate your setup
- Check Supabase dashboard for user management
- Review audit logs for security monitoring