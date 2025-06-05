#!/usr/bin/env python3
"""
Generate secure credentials for TKR News Gatherer
Creates JWT secret keys, API keys, and other security tokens
"""

import secrets
import string
import hashlib
import base64
import os
from datetime import datetime

def generate_jwt_secret(length=32):
    """Generate a secure JWT secret key"""
    return secrets.token_urlsafe(length)

def generate_api_key(prefix="tkr", length=32):
    """Generate a secure API key with prefix"""
    random_part = secrets.token_urlsafe(length)
    return f"{prefix}_{random_part}"

def generate_password(length=16):
    """Generate a secure password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_hash(data):
    """Generate SHA256 hash of data"""
    return hashlib.sha256(data.encode()).hexdigest()

def main():
    print("🔐 TKR News Gatherer Credential Generator")
    print("=========================================")
    print()
    
    # Generate JWT secret
    jwt_secret = generate_jwt_secret()
    print(f"JWT Secret Key:")
    print(f"JWT_SECRET_KEY={jwt_secret}")
    print()
    
    # Generate API keys
    print("API Keys (use any of these for X-API-Key header):")
    for i in range(3):
        api_key = generate_api_key()
        print(f"API_KEY_{i+1}={api_key}")
    
    # Combined API keys for environment variable
    api_keys = [generate_api_key() for _ in range(3)]
    print()
    print("Combined API Keys for .env file:")
    print(f"API_KEYS={','.join(api_keys)}")
    print()
    
    # Generate admin password
    admin_password = generate_password()
    print(f"Admin Password:")
    print(f"ADMIN_PASSWORD={admin_password}")
    print()
    
    # Generate database encryption key
    db_key = generate_jwt_secret(32)
    print(f"Database Encryption Key:")
    print(f"DB_ENCRYPTION_KEY={db_key}")
    print()
    
    # Generate session secrets
    session_secret = generate_jwt_secret(64)
    print(f"Session Secret:")
    print(f"SESSION_SECRET={session_secret}")
    print()
    
    print("🔒 Security Recommendations:")
    print("=============================")
    print("1. Store these credentials securely (use a password manager)")
    print("2. Never commit real credentials to version control")
    print("3. Use different credentials for each environment")
    print("4. Rotate credentials regularly (at least every 90 days)")
    print("5. Consider using a secrets management service for production")
    print()
    
    print("📝 .env File Template:")
    print("======================")
    print(f"""# Security credentials generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
JWT_SECRET_KEY={jwt_secret}
API_KEYS={','.join(api_keys)}
ADMIN_PASSWORD={admin_password}
DB_ENCRYPTION_KEY={db_key}
SESSION_SECRET={session_secret}

# Rate limiting
RATE_LIMIT_PER_MINUTE=100

# CORS (update with your actual domains)
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Security headers
ENABLE_SECURITY_HEADERS=true

# Trusted hosts (update with your actual domains)
TRUSTED_HOSTS=yourdomain.com,*.yourdomain.com
""")
    
    print()
    print("⚠️  Important Security Notes:")
    print("============================")
    print("- Replace 'yourdomain.com' with your actual domain")
    print("- Remove localhost origins in production")
    print("- Consider implementing proper user management")
    print("- Enable HTTPS in production")
    print("- Regularly audit access logs")
    print("- Implement proper backup and recovery procedures")

if __name__ == "__main__":
    main()