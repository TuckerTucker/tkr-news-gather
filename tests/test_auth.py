#!/usr/bin/env python3
"""
Test script for Supabase Authentication implementation
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.config import Config
from src.utils.supabase_auth import SupabaseAuth, UserRegistration, UserLogin

async def test_authentication():
    """Test the authentication system"""
    load_dotenv()
    
    # Initialize config and auth
    config = Config()
    auth = SupabaseAuth(config)
    
    if not auth.is_available():
        print("❌ Supabase Auth not available - check configuration")
        return False
    
    print("✅ Supabase Auth initialized successfully")
    
    # Test user data
    test_email = "test@example.com"
    test_password = "SecurePassword123!"
    test_name = "Test User"
    
    try:
        # Test 1: User Registration
        print("\n🔧 Testing user registration...")
        registration_data = UserRegistration(
            email=test_email,
            password=test_password,
            full_name=test_name,
            role="user"
        )
        
        try:
            registration_result = await auth.register_user(registration_data)
            print(f"✅ Registration successful: {registration_result}")
        except Exception as e:
            if "already registered" in str(e).lower():
                print(f"ℹ️  User already exists: {test_email}")
            else:
                print(f"❌ Registration failed: {e}")
                return False
        
        # Test 2: User Login
        print("\n🔧 Testing user login...")
        login_data = UserLogin(
            email=test_email,
            password=test_password
        )
        
        try:
            token_result = await auth.login_user(login_data)
            print(f"✅ Login successful")
            print(f"   Token type: {token_result.token_type}")
            print(f"   Expires in: {token_result.expires_in} seconds")
            
            # Test 3: Token Verification
            print("\n🔧 Testing token verification...")
            user = await auth.verify_token(token_result.access_token)
            print(f"✅ Token verification successful")
            print(f"   User ID: {user.id}")
            print(f"   Email: {user.email}")
            print(f"   Role: {user.role}")
            print(f"   Scopes: {user.scopes}")
            print(f"   Email confirmed: {user.email_confirmed}")
            
            # Test 4: Logout
            print("\n🔧 Testing user logout...")
            logout_success = await auth.logout_user(token_result.access_token)
            print(f"✅ Logout {'successful' if logout_success else 'failed'}")
            
            return True
            
        except Exception as e:
            print(f"❌ Login failed: {e}")
            return False
    
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        return False

def test_database_migration():
    """Test database migration requirements"""
    migration_file = "database/auth_migration.sql"
    
    if os.path.exists(migration_file):
        print(f"✅ Database migration file exists: {migration_file}")
        
        with open(migration_file, 'r') as f:
            content = f.read()
            
        # Check for key components
        checks = [
            ("user_profiles table", "CREATE TABLE user_profiles"),
            ("RLS policies", "ENABLE ROW LEVEL SECURITY"),
            ("Auth trigger", "CREATE TRIGGER on_auth_user_created"),
            ("Audit logging", "CREATE TABLE user_audit_log"),
            ("Role functions", "CREATE OR REPLACE FUNCTION get_user_role")
        ]
        
        for check_name, check_content in checks:
            if check_content in content:
                print(f"✅ {check_name} found in migration")
            else:
                print(f"❌ {check_name} missing from migration")
                return False
        
        return True
    else:
        print(f"❌ Database migration file not found: {migration_file}")
        return False

def test_configuration():
    """Test configuration requirements"""
    config = Config()
    
    checks = [
        ("SUPABASE_URL", config.SUPABASE_URL),
        ("SUPABASE_ANON_KEY", config.SUPABASE_ANON_KEY),
    ]
    
    all_good = True
    for name, value in checks:
        if value:
            print(f"✅ {name} configured")
        else:
            print(f"❌ {name} not configured")
            all_good = False
    
    return all_good

async def main():
    """Run all tests"""
    print("🧪 TKR News Gather - Authentication Tests")
    print("=" * 50)
    
    # Test 1: Configuration
    print("\n1️⃣ Testing Configuration...")
    config_ok = test_configuration()
    
    # Test 2: Database Migration
    print("\n2️⃣ Testing Database Migration...")
    migration_ok = test_database_migration()
    
    # Test 3: Authentication Flow
    print("\n3️⃣ Testing Authentication Flow...")
    if config_ok:
        auth_ok = await test_authentication()
    else:
        print("⚠️  Skipping authentication tests due to configuration issues")
        auth_ok = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"   Configuration: {'✅' if config_ok else '❌'}")
    print(f"   Database Migration: {'✅' if migration_ok else '❌'}")
    print(f"   Authentication: {'✅' if auth_ok else '❌'}")
    
    if config_ok and migration_ok and auth_ok:
        print("\n🎉 All tests passed! Authentication system is ready.")
        return True
    else:
        print("\n⚠️  Some tests failed. Please check the configuration and setup.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)