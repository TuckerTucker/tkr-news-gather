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

def update_env_file(credentials):
    """Update .env file with generated credentials while preserving format from .env.example"""
    project_dir = os.path.dirname(os.path.dirname(__file__))
    env_file = os.path.join(project_dir, '.env')
    env_example_file = os.path.join(project_dir, '.env.example')
    
    # Read existing .env if it exists, otherwise use .env.example as template
    template_file = env_file if os.path.exists(env_file) else env_example_file
    
    if not os.path.exists(template_file):
        raise Exception(f"Neither .env nor .env.example found in {project_dir}")
    
    # Read the template/existing file
    with open(template_file, 'r') as f:
        lines = f.readlines()
    
    # Parse existing values from .env if it exists
    existing_values = {}
    if os.path.exists(env_file) and env_file != template_file:
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    existing_values[key.strip()] = value.strip()
    
    # Write the updated .env file
    with open(env_file, 'w') as f:
        # Update the header timestamp
        for line in lines:
            line = line.rstrip()
            
            # Update header timestamp
            if line.startswith('# Updated:'):
                f.write(f"# Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Security credentials generated\n")
                continue
            
            # Process environment variable lines
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                
                # Use generated credential if available
                if key in credentials:
                    f.write(f"{key}={credentials[key]}\n")
                # Use existing value if available (preserves user settings)
                elif key in existing_values:
                    f.write(f"{key}={existing_values[key]}\n")
                # Keep the template value
                else:
                    f.write(line + '\n')
            else:
                # Keep comments and blank lines as-is
                f.write(line + '\n')
        
        # Add generation timestamp
        f.write(f"\n# Security credentials generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    return env_file

def main():
    print("🔐 TKR News Gatherer Credential Generator")
    print("=========================================")
    print()
    
    # Generate all credentials
    jwt_secret = generate_jwt_secret()
    api_keys = [generate_api_key() for _ in range(3)]
    admin_password = generate_password()
    db_key = generate_jwt_secret(32)
    session_secret = generate_jwt_secret(64)
    
    # Create credentials dictionary
    credentials = {
        'JWT_SECRET_KEY': jwt_secret,
        'API_KEYS': ','.join(api_keys),
        'ADMIN_PASSWORD': admin_password,
        'DB_ENCRYPTION_KEY': db_key,
        'SESSION_SECRET': session_secret
    }
    
    # Display generated credentials
    print(f"JWT Secret Key:")
    print(f"JWT_SECRET_KEY={jwt_secret}")
    print()
    
    print("API Keys (use any of these for X-API-Key header):")
    for i, api_key in enumerate(api_keys, 1):
        print(f"API_KEY_{i}={api_key}")
    
    print()
    print("Combined API Keys for .env file:")
    print(f"API_KEYS={','.join(api_keys)}")
    print()
    
    print(f"Admin Password:")
    print(f"ADMIN_PASSWORD={admin_password}")
    print()
    
    print(f"Database Encryption Key:")
    print(f"DB_ENCRYPTION_KEY={db_key}")
    print()
    
    print(f"Session Secret:")
    print(f"SESSION_SECRET={session_secret}")
    print()
    
    # Update .env file
    try:
        env_file = update_env_file(credentials)
        print(f"✅ Credentials saved to: {env_file}")
        print()
    except Exception as e:
        print(f"❌ Failed to update .env file: {str(e)}")
        print("Please manually copy the credentials above to your .env file.")
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