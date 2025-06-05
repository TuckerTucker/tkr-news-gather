"""
Supabase Authentication Module for TKR News Gather
Implements secure user authentication using Supabase Auth
"""

from supabase import create_client, Client
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import jwt
from pydantic import BaseModel, EmailStr
import asyncio
from .logger import get_logger

logger = get_logger(__name__)

# Pydantic models for auth
class UserRegistration(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: str = "user"  # user, admin

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    role: str
    email_confirmed: bool
    created_at: datetime
    scopes: List[str] = []

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None

security = HTTPBearer()

class SupabaseAuth:
    def __init__(self, config):
        self.config = config
        if not config.SUPABASE_URL or not config.SUPABASE_ANON_KEY:
            logger.warning("Supabase credentials not found. Authentication will fail.")
            self.client = None
            return
            
        self.client: Client = create_client(
            config.SUPABASE_URL,
            config.SUPABASE_ANON_KEY
        )
        
        # Role-based scopes mapping
        self.role_scopes = {
            "user": ["read"],
            "editor": ["read", "write"],
            "admin": ["read", "write", "admin"]
        }
    
    def is_available(self) -> bool:
        """Check if Supabase Auth is available"""
        return self.client is not None
    
    async def register_user(self, user_data: UserRegistration) -> Dict[str, Any]:
        """Register a new user with Supabase Auth"""
        if not self.is_available():
            raise HTTPException(
                status_code=503,
                detail="Authentication service unavailable"
            )
        
        try:
            # Register with Supabase Auth
            response = self.client.auth.sign_up({
                "email": user_data.email,
                "password": user_data.password,
                "options": {
                    "data": {
                        "full_name": user_data.full_name,
                        "role": user_data.role
                    }
                }
            })
            
            if response.user:
                logger.info(f"User registered successfully: {user_data.email}")
                
                # Create user profile in our database
                await self._create_user_profile(response.user, user_data)
                
                return {
                    "user_id": response.user.id,
                    "email": response.user.email,
                    "email_confirmed": response.user.email_confirmed_at is not None,
                    "message": "Registration successful. Please check your email to confirm your account."
                }
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Registration failed"
                )
                
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            if "already registered" in str(e).lower():
                raise HTTPException(
                    status_code=409,
                    detail="User with this email already exists"
                )
            raise HTTPException(
                status_code=400,
                detail=f"Registration failed: {str(e)}"
            )
    
    async def login_user(self, login_data: UserLogin) -> Token:
        """Authenticate user and return JWT token"""
        if not self.is_available():
            raise HTTPException(
                status_code=503,
                detail="Authentication service unavailable"
            )
        
        try:
            # Authenticate with Supabase
            response = self.client.auth.sign_in_with_password({
                "email": login_data.email,
                "password": login_data.password
            })
            
            if response.user and response.session:
                logger.info(f"User logged in successfully: {login_data.email}")
                
                # Get user profile for additional data
                user_profile = await self._get_user_profile(response.user.id)
                
                return Token(
                    access_token=response.session.access_token,
                    token_type="bearer",
                    expires_in=response.session.expires_in or 3600,
                    refresh_token=response.session.refresh_token
                )
            else:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid credentials"
                )
                
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            # Consistent delay to prevent timing attacks
            await asyncio.sleep(0.1)
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials"
            )
    
    async def verify_token(self, token: str) -> User:
        """Verify JWT token and return user information"""
        if not self.is_available():
            raise HTTPException(
                status_code=503,
                detail="Authentication service unavailable"
            )
        
        try:
            # Set the session token
            self.client.auth.set_session(token, "")
            
            # Get the current user
            user_response = self.client.auth.get_user(token)
            
            if user_response.user:
                user_profile = await self._get_user_profile(user_response.user.id)
                role = user_profile.get("role", "user") if user_profile else "user"
                
                return User(
                    id=user_response.user.id,
                    email=user_response.user.email,
                    full_name=user_profile.get("full_name") if user_profile else None,
                    role=role,
                    email_confirmed=user_response.user.email_confirmed_at is not None,
                    created_at=datetime.fromisoformat(user_response.user.created_at.replace('Z', '+00:00')),
                    scopes=self.role_scopes.get(role, ["read"])
                )
            else:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid or expired token"
                )
                
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token"
            )
    
    async def refresh_token(self, refresh_token: str) -> Token:
        """Refresh access token using refresh token"""
        if not self.is_available():
            raise HTTPException(
                status_code=503,
                detail="Authentication service unavailable"
            )
        
        try:
            response = self.client.auth.refresh_session(refresh_token)
            
            if response.session:
                return Token(
                    access_token=response.session.access_token,
                    token_type="bearer",
                    expires_in=response.session.expires_in or 3600,
                    refresh_token=response.session.refresh_token
                )
            else:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid refresh token"
                )
                
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            raise HTTPException(
                status_code=401,
                detail="Invalid refresh token"
            )
    
    async def logout_user(self, token: str) -> bool:
        """Logout user and invalidate token"""
        if not self.is_available():
            return False
        
        try:
            self.client.auth.set_session(token, "")
            self.client.auth.sign_out()
            return True
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return False
    
    async def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> bool:
        """Update user profile information"""
        if not self.is_available():
            return False
        
        try:
            result = self.client.table("user_profiles").update(profile_data).eq("user_id", user_id).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Profile update error: {str(e)}")
            return False
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user account (admin only)"""
        if not self.is_available():
            return False
        
        try:
            # Delete user profile first
            self.client.table("user_profiles").delete().eq("user_id", user_id).execute()
            
            # Note: Supabase doesn't allow deleting auth users via client
            # This would need to be done via admin API or dashboard
            logger.info(f"User profile deleted for: {user_id}")
            return True
        except Exception as e:
            logger.error(f"User deletion error: {str(e)}")
            return False
    
    async def _create_user_profile(self, user: Any, user_data: UserRegistration) -> None:
        """Create user profile in our database"""
        try:
            profile_data = {
                "user_id": user.id,
                "email": user.email,
                "full_name": user_data.full_name,
                "role": user_data.role,
                "created_at": datetime.utcnow().isoformat()
            }
            
            self.client.table("user_profiles").insert(profile_data).execute()
            logger.info(f"User profile created for: {user.email}")
            
        except Exception as e:
            logger.error(f"Error creating user profile: {str(e)}")
    
    async def _get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile from our database"""
        try:
            result = self.client.table("user_profiles").select("*").eq("user_id", user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error getting user profile: {str(e)}")
            return None

# Dependency functions for FastAPI
def get_supabase_auth(config=None):
    """Get Supabase Auth instance"""
    from .config import Config
    if config is None:
        config = Config()
    return SupabaseAuth(config)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth: SupabaseAuth = Depends(get_supabase_auth)
) -> User:
    """Get current authenticated user"""
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    
    return await auth.verify_token(credentials.credentials)

def require_scope(required_scope: str):
    """Dependency factory for scope-based authorization"""
    def scope_checker(current_user: User = Depends(get_current_user)) -> User:
        if required_scope not in current_user.scopes:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required scope: {required_scope}"
            )
        return current_user
    return scope_checker

async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin role"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    return current_user

async def require_confirmed_email(current_user: User = Depends(get_current_user)) -> User:
    """Require confirmed email address"""
    if not current_user.email_confirmed:
        raise HTTPException(
            status_code=403,
            detail="Email confirmation required"
        )
    return current_user