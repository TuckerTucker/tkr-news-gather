"""
Security utilities for TKR News Gatherer
Implements JWT authentication, rate limiting, input validation, and security headers
"""

import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse

import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator, HttpUrl
import ipaddress

from .config import Config
from .logger import get_logger

logger = get_logger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Security bearer for JWT
security = HTTPBearer()

class SecurityConfig:
    """Security configuration and settings"""
    
    def __init__(self, config: Config):
        self.config = config
        self.secret_key = config.JWT_SECRET_KEY or self._generate_secret_key()
        self.api_keys = self._load_api_keys()
        
    def _generate_secret_key(self) -> str:
        """Generate a secure random secret key"""
        return secrets.token_urlsafe(32)
    
    def _load_api_keys(self) -> List[str]:
        """Load valid API keys from configuration"""
        keys = self.config.API_KEYS or ""
        return [key.strip() for key in keys.split(",") if key.strip()]

class Token(BaseModel):
    """JWT token response model"""
    access_token: str
    token_type: str
    expires_in: int

class TokenData(BaseModel):
    """JWT token payload data"""
    username: Optional[str] = None
    scopes: List[str] = []

class User(BaseModel):
    """User model for authentication"""
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
    scopes: List[str] = []

class SecureUrlValidator:
    """Validates URLs to prevent SSRF attacks"""
    
    BLOCKED_SCHEMES = ["file", "ftp", "gopher", "data"]
    BLOCKED_HOSTS = [
        "localhost", "127.0.0.1", "0.0.0.0",
        "169.254.169.254",  # AWS metadata
        "metadata.google.internal",  # GCP metadata
    ]
    BLOCKED_NETWORKS = [
        ipaddress.ip_network("10.0.0.0/8"),      # Private Class A
        ipaddress.ip_network("172.16.0.0/12"),   # Private Class B  
        ipaddress.ip_network("192.168.0.0/16"),  # Private Class C
        ipaddress.ip_network("127.0.0.0/8"),     # Loopback
        ipaddress.ip_network("169.254.0.0/16"),  # Link-local
        ipaddress.ip_network("224.0.0.0/4"),     # Multicast
    ]
    
    @classmethod
    def validate_url(cls, url: str) -> bool:
        """Validate URL against SSRF threats"""
        try:
            parsed = urlparse(str(url))
            
            # Check scheme
            if parsed.scheme.lower() in cls.BLOCKED_SCHEMES:
                logger.warning(f"Blocked URL scheme: {parsed.scheme}")
                return False
            
            # Check hostname
            hostname = parsed.hostname
            if not hostname:
                return False
                
            if hostname.lower() in cls.BLOCKED_HOSTS:
                logger.warning(f"Blocked hostname: {hostname}")
                return False
            
            # Check IP addresses
            try:
                ip = ipaddress.ip_address(hostname)
                for network in cls.BLOCKED_NETWORKS:
                    if ip in network:
                        logger.warning(f"Blocked IP in private network: {ip}")
                        return False
            except ValueError:
                # Not an IP address, continue with hostname validation
                pass
            
            # Check for localhost variants
            if any(blocked in hostname.lower() for blocked in 
                   ["localhost", "local", "internal", "intranet"]):
                logger.warning(f"Blocked hostname variant: {hostname}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"URL validation error: {e}")
            return False

class AuthenticationHandler:
    """Handles JWT authentication and API key validation"""
    
    def __init__(self, security_config: SecurityConfig):
        self.config = security_config
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Generate password hash"""
        return pwd_context.hash(password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(
            to_encode, 
            self.config.secret_key, 
            algorithm=ALGORITHM
        )
        return encoded_jwt
    
    def verify_token(self, token: str) -> TokenData:
        """Verify and decode JWT token"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(
                token, 
                self.config.secret_key, 
                algorithms=[ALGORITHM]
            )
            username: str = payload.get("sub")
            scopes: List[str] = payload.get("scopes", [])
            
            if username is None:
                raise credentials_exception
                
            token_data = TokenData(username=username, scopes=scopes)
            return token_data
            
        except jwt.PyJWTError as e:
            logger.warning(f"JWT validation failed: {e}")
            raise credentials_exception
    
    def verify_api_key(self, api_key: str) -> bool:
        """Verify API key"""
        if not self.config.api_keys:
            return False
        
        # Use constant-time comparison to prevent timing attacks
        for valid_key in self.config.api_keys:
            if secrets.compare_digest(api_key, valid_key):
                return True
        return False

class InputValidator:
    """Enhanced input validation for security"""
    
    ALLOWED_PROVINCES = [
        "alberta", "british columbia", "manitoba", "new brunswick",
        "newfoundland and labrador", "northwest territories", 
        "nova scotia", "nunavut", "ontario", "prince edward island",
        "quebec", "saskatchewan", "yukon"
    ]
    
    @classmethod
    def validate_province(cls, province: str) -> str:
        """Validate province input"""
        normalized = province.lower().strip()
        if normalized not in cls.ALLOWED_PROVINCES:
            raise ValueError(f"Invalid province: {province}")
        return normalized
    
    @classmethod
    def validate_limit(cls, limit: int) -> int:
        """Validate article limit"""
        if not isinstance(limit, int) or limit < 1 or limit > 50:
            raise ValueError("Limit must be between 1 and 50")
        return limit
    
    @classmethod
    def validate_host_type(cls, host_type: str) -> str:
        """Validate AI host type"""
        allowed_hosts = ["anchor", "friend", "newsreel"]
        if host_type not in allowed_hosts:
            raise ValueError(f"Invalid host type. Allowed: {allowed_hosts}")
        return host_type

# Enhanced Pydantic models with security validation
class SecureNewsRequest(BaseModel):
    """Secure news request with validation"""
    province: str
    limit: int = 10
    scrape: bool = True
    
    @validator('province')
    def validate_province(cls, v):
        return InputValidator.validate_province(v)
    
    @validator('limit')
    def validate_limit(cls, v):
        return InputValidator.validate_limit(v)

class SecureUrlScrapeRequest(BaseModel):
    """Secure URL scraping request with SSRF protection"""
    urls: List[HttpUrl]
    
    @validator('urls')
    def validate_urls(cls, v):
        if len(v) > 20:
            raise ValueError('Maximum 20 URLs allowed per request')
        
        for url in v:
            if not SecureUrlValidator.validate_url(str(url)):
                raise ValueError(f'URL not allowed for security reasons: {url}')
        
        return v

class SecureProcessRequest(BaseModel):
    """Secure processing request with validation"""
    articles: List[Dict[str, Any]]
    host_type: str
    province: str
    
    @validator('host_type')
    def validate_host_type(cls, v):
        return InputValidator.validate_host_type(v)
    
    @validator('province')
    def validate_province(cls, v):
        return InputValidator.validate_province(v)
    
    @validator('articles')
    def validate_articles(cls, v):
        if len(v) > 50:
            raise ValueError('Maximum 50 articles allowed per request')
        return v

# Security dependencies for FastAPI
def get_security_config() -> SecurityConfig:
    """Get security configuration"""
    config = Config()
    return SecurityConfig(config)

def get_auth_handler(security_config: SecurityConfig = Depends(get_security_config)) -> AuthenticationHandler:
    """Get authentication handler"""
    return AuthenticationHandler(security_config)

async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_handler: AuthenticationHandler = Depends(get_auth_handler)
) -> TokenData:
    """Verify JWT token dependency"""
    return auth_handler.verify_token(credentials.credentials)

async def verify_api_key(
    request: Request,
    auth_handler: AuthenticationHandler = Depends(get_auth_handler)
) -> bool:
    """Verify API key from header"""
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    if not auth_handler.verify_api_key(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return True

async def get_current_user(token_data: TokenData = Depends(verify_token)) -> User:
    """Get current authenticated user"""
    # In a real implementation, you would fetch user from database
    user = User(
        username=token_data.username,
        scopes=token_data.scopes
    )
    
    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user

def require_scope(required_scope: str):
    """Decorator for requiring specific scope"""
    def scope_checker(user: User = Depends(get_current_user)):
        if required_scope not in user.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires '{required_scope}' scope"
            )
        return user
    return scope_checker

# Rate limiting helper
def create_rate_limiter():
    """Create rate limiter instance"""
    from slowapi import Limiter
    from slowapi.util import get_remote_address
    
    return Limiter(
        key_func=get_remote_address,
        default_limits=["100/minute"]
    )