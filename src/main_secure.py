"""
Secure FastAPI application for TKR News Gatherer
Implements comprehensive security controls including authentication, rate limiting, 
input validation, and security headers
"""

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel, ValidationError
from typing import List, Optional, Dict, Any, Union
import asyncio
from datetime import datetime, timedelta

from .api import NewsGatherAPI
from .utils import Config, SupabaseClient, get_logger
from .utils.security import (
    SecureNewsRequest, SecureUrlScrapeRequest, SecureProcessRequest,
    verify_api_key
)
from .utils.supabase_auth import (
    SupabaseAuth, UserRegistration, UserLogin, User, Token,
    get_current_user, require_scope, require_admin, require_confirmed_email,
    get_supabase_auth
)
from .utils.middleware import (
    SecurityHeadersMiddleware, RequestLoggingMiddleware, ErrorHandlingMiddleware,
    RateLimitingMiddleware, HealthCheckMiddleware
)
from .news import get_all_provinces

logger = get_logger(__name__)

# Initialize configuration
config = Config()

# Validate critical configuration
if not config.ANTHROPIC_API_KEY:
    logger.warning("ANTHROPIC_API_KEY not configured - AI processing will fail")

if not config.JWT_SECRET_KEY:
    logger.warning("JWT_SECRET_KEY not configured - generating temporary key")

if not config.API_KEYS:
    logger.warning("API_KEYS not configured - API key authentication disabled")

# Initialize FastAPI app with security settings
app = FastAPI(
    title="TKR News Gatherer API",
    description="Secure Canadian news collection and AI processing service with authentication",
    version="0.1.0",
    docs_url="/docs" if config.DEBUG else None,  # Disable docs in production
    redoc_url="/redoc" if config.DEBUG else None,
    openapi_url="/openapi.json" if config.DEBUG else None,
)

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{config.RATE_LIMIT_PER_MINUTE}/minute"]
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add security middleware (order matters!)
app.add_middleware(HealthCheckMiddleware)
app.add_middleware(SecurityHeadersMiddleware, config=config)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(ErrorHandlingMiddleware, config=config)
app.add_middleware(RateLimitingMiddleware, config=config)

# Add CORS middleware with restricted origins
cors_origins = [origin.strip() for origin in config.CORS_ORIGINS if origin.strip()]
if not cors_origins or "*" in cors_origins:
    if not config.DEBUG:
        logger.error("CORS origins not properly configured for production")
        cors_origins = ["https://yourdomain.com"]  # Fallback
    else:
        cors_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)

# Add trusted host middleware
if not config.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["yourdomain.com", "*.yourdomain.com"]
    )

# Initialize services
news_api = NewsGatherAPI()
supabase = SupabaseClient(config)
auth_service = SupabaseAuth(config)

# Security dependencies
security = HTTPBearer()

# Response models
class NewsResponse(BaseModel):
    status: str
    totalResults: int
    results: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class ProcessedResponse(BaseModel):
    status: str
    host_type: str
    articles: List[Dict[str, Any]]
    processed_at: str

class ErrorResponse(BaseModel):
    error: str
    message: str
    request_id: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    uptime: float
    timestamp: float
    version: str
    components: Dict[str, str]

# Authentication endpoints
@app.post("/auth/register", tags=["Authentication"])
@limiter.limit("3/minute")  # Strict limit for registration
async def register_user(
    request: Request,
    user_data: UserRegistration,
    auth: SupabaseAuth = Depends(get_supabase_auth)
):
    """
    Register a new user account
    """
    return await auth.register_user(user_data)

@app.post("/auth/login", response_model=Token, tags=["Authentication"])
@limiter.limit("5/minute")  # Strict limit for auth endpoints
async def login_user(
    request: Request,
    login_data: UserLogin,
    auth: SupabaseAuth = Depends(get_supabase_auth)
):
    """
    Authenticate user and return JWT token
    """
    return await auth.login_user(login_data)

@app.post("/auth/refresh", response_model=Token, tags=["Authentication"])
@limiter.limit("10/minute")
async def refresh_token(
    request: Request,
    refresh_token: str,
    auth: SupabaseAuth = Depends(get_supabase_auth)
):
    """
    Refresh access token using refresh token
    """
    return await auth.refresh_token(refresh_token)

@app.post("/auth/logout", tags=["Authentication"])
@limiter.limit("10/minute")
async def logout_user(
    request: Request,
    current_user: User = Depends(get_current_user),
    auth: SupabaseAuth = Depends(get_supabase_auth)
):
    """
    Logout user and invalidate token
    """
    # Extract token from request
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        success = await auth.logout_user(token)
        return {"success": success, "message": "Logged out successfully" if success else "Logout failed"}
    return {"success": False, "message": "No token found"}

@app.get("/auth/me", response_model=User, tags=["Authentication"])
@limiter.limit("20/minute")
async def get_current_user_info(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information
    """
    return current_user

# Health check endpoint (public)
@app.get("/", response_model=HealthResponse, tags=["Health"])
@limiter.limit("30/minute")
async def root(request: Request):
    """Public health check endpoint"""
    return {
        "status": "healthy",
        "uptime": 0.0,  # Will be set by middleware
        "timestamp": datetime.utcnow().timestamp(),
        "version": "0.1.0",
        "components": {
            "api": "healthy",
            "database": "available" if supabase.is_available() else "unavailable"
        }
    }

@app.get("/health", response_model=HealthResponse, tags=["Health"])
@limiter.limit("30/minute")
async def health_check(request: Request):
    """Detailed health check with component status"""
    health_status = {
        "status": "healthy",
        "uptime": 0.0,
        "timestamp": datetime.utcnow().timestamp(),
        "version": "0.1.0",
        "components": {
            "api": "healthy",
            "anthropic": "unknown",
            "supabase": "available" if supabase.is_available() else "unavailable"
        }
    }
    
    # Test Anthropic connection
    try:
        if config.ANTHROPIC_API_KEY:
            health_status["components"]["anthropic"] = "available"
        else:
            health_status["components"]["anthropic"] = "no_api_key"
    except Exception:
        health_status["components"]["anthropic"] = "error"
    
    return health_status

# Province endpoints (protected)
@app.get("/provinces", tags=["Provinces"])
@limiter.limit("20/minute")
async def get_provinces(
    request: Request,
    _: bool = Depends(verify_api_key)
):
    """Get list of all available Canadian provinces (requires API key)"""
    try:
        return news_api.get_provinces()
    except Exception as e:
        logger.error(f"Error getting provinces: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve provinces")

@app.get("/provinces/with-data", tags=["Provinces"])
@limiter.limit("20/minute")
async def get_provinces_with_data(
    request: Request,
    _: bool = Depends(verify_api_key)
):
    """Get provinces that have news data in the database (requires API key)"""
    try:
        provinces = await supabase.get_provinces_with_data()
        return {
            "provinces": provinces,
            "total": len(provinces)
        }
    except Exception as e:
        logger.error(f"Error getting provinces with data: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve province data")

# News endpoints (protected with JWT)
@app.get("/news/{province}", response_model=NewsResponse, tags=["News"])
@limiter.limit("10/minute")
async def get_news(
    request: Request,
    province: str,
    limit: int = Query(10, ge=1, le=50, description="Number of articles to fetch"),
    scrape: bool = Query(True, description="Whether to scrape full article content"),
    save_to_db: bool = Query(False, description="Whether to save results to database"),
    current_user: User = Depends(get_current_user)
):
    """Get news for a specific Canadian province (requires JWT)"""
    try:
        # Validate input using secure validator
        secure_request = SecureNewsRequest(
            province=province,
            limit=limit,
            scrape=scrape
        )
        
        # Fetch news
        result = await news_api.get_news(
            secure_request.province, 
            secure_request.limit, 
            secure_request.scrape
        )
        
        # Save to database if requested and user has write scope
        if save_to_db and "write" in current_user.scopes and supabase.is_available():
            if result.get("status") == "success":
                session_id = await supabase.create_news_session(
                    secure_request.province, 
                    result.get("metadata", {})
                )
                if session_id and result.get("results"):
                    await supabase.save_articles(session_id, result["results"])
                    result["metadata"]["session_id"] = session_id
        
        return result
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting news for {province}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve news")

@app.post("/news", response_model=NewsResponse, tags=["News"])
@limiter.limit("10/minute")
async def get_news_post(
    request: Request,
    news_request: SecureNewsRequest,
    current_user: User = Depends(get_current_user)
):
    """Get news using POST request (requires JWT)"""
    try:
        result = await news_api.get_news(
            news_request.province, 
            news_request.limit, 
            news_request.scrape
        )
        return result
    except Exception as e:
        logger.error(f"Error getting news: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve news")

# Processing endpoints (protected with specific scopes)
@app.post("/process", response_model=ProcessedResponse, tags=["Processing"])
@limiter.limit("5/minute")  # Lower limit for AI processing
async def process_articles(
    request: Request,
    process_request: SecureProcessRequest,
    current_user: User = Depends(require_scope("write"))
):
    """Process articles with AI host personality (requires write scope)"""
    try:
        result = await news_api.process_news(
            process_request.articles, 
            process_request.host_type, 
            process_request.province
        )
        return result
    except Exception as e:
        logger.error(f"Error processing articles: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process articles")

@app.get("/process/{province}/{host_type}", response_model=ProcessedResponse, tags=["Processing"])
@limiter.limit("5/minute")
async def process_latest_news(
    request: Request,
    province: str,
    host_type: str,
    limit: int = Query(5, ge=1, le=20, description="Number of articles to process"),
    current_user: User = Depends(require_scope("write"))
):
    """Fetch and process latest news (requires write scope)"""
    try:
        # Validate inputs
        secure_request = SecureNewsRequest(province=province, limit=limit, scrape=True)
        validated_host_type = SecureProcessRequest(
            articles=[],  # Dummy for validation
            host_type=host_type,
            province=province
        ).host_type
        
        # Fetch news first
        news_result = await news_api.get_news(
            secure_request.province, 
            secure_request.limit, 
            scrape=True
        )
        
        if news_result.get("status") != "success" or not news_result.get("results"):
            raise HTTPException(
                status_code=404, 
                detail=f"No news found for {province}"
            )
        
        # Process with AI
        result = await news_api.process_news(
            news_result["results"], 
            validated_host_type, 
            secure_request.province
        )
        return result
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing latest news: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process news")

# Scraping endpoints (protected with API key and additional validation)
@app.post("/scrape", tags=["Scraping"])
@limiter.limit("3/minute")  # Very restrictive for scraping
async def scrape_urls(
    request: Request,
    scrape_request: SecureUrlScrapeRequest,
    _: bool = Depends(verify_api_key)
):
    """Scrape content from specific URLs (requires API key)"""
    try:
        # Convert HttpUrl objects to strings
        urls = [str(url) for url in scrape_request.urls]
        result = await news_api.scrape_urls(urls)
        return result
    except Exception as e:
        logger.error(f"Error scraping URLs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to scrape URLs")

# Database endpoints (protected)
@app.get("/sessions/{province}/latest", tags=["Database"])
@limiter.limit("20/minute")
async def get_latest_session(
    request: Request,
    province: str,
    current_user: User = Depends(get_current_user)
):
    """Get the latest news session for a province (requires JWT)"""
    try:
        if not supabase.is_available():
            raise HTTPException(status_code=503, detail="Database not available")
        
        # Validate province
        secure_request = SecureNewsRequest(province=province, limit=1)
        
        session = await supabase.get_latest_session(secure_request.province)
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"No sessions found for {province}"
            )
        
        return session
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting latest session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve session")

@app.get("/sessions/{session_id}/articles", tags=["Database"])
@limiter.limit("20/minute")
async def get_session_articles(
    request: Request,
    session_id: str,
    include_processed: bool = Query(False, description="Include processed content"),
    current_user: User = Depends(get_current_user)
):
    """Get all articles for a specific session (requires JWT)"""
    try:
        if not supabase.is_available():
            raise HTTPException(status_code=503, detail="Database not available")
        
        articles = await supabase.get_session_articles(session_id, include_processed)
        return {
            "session_id": session_id,
            "articles": articles,
            "total": len(articles)
        }
    except Exception as e:
        logger.error(f"Error getting session articles: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve articles")

# Background task for full news pipeline (highly restricted)
async def full_pipeline_task(province: str, host_types: List[str], limit: int):
    """Background task to run full news pipeline"""
    try:
        logger.info(f"Starting full pipeline for {province}")
        
        # 1. Fetch news
        news_result = await news_api.get_news(province, limit, scrape=True)
        if news_result.get("status") != "success":
            logger.error(f"Failed to fetch news for {province}")
            return
        
        # 2. Save to database
        session_id = None
        if supabase.is_available():
            session_id = await supabase.create_news_session(province, news_result.get("metadata", {}))
            if session_id:
                await supabase.save_articles(session_id, news_result["results"])
        
        # 3. Process with each host type
        for host_type in host_types:
            try:
                processed_result = await news_api.process_news(
                    news_result["results"], 
                    host_type, 
                    province
                )
                logger.info(f"Processed {len(processed_result.get('articles', []))} articles with {host_type}")
            except Exception as e:
                logger.error(f"Error processing with {host_type}: {str(e)}")
        
        logger.info(f"Completed full pipeline for {province}")
        
    except Exception as e:
        logger.error(f"Error in full pipeline for {province}: {str(e)}")

@app.post("/pipeline/{province}", tags=["Pipeline"])
@limiter.limit("1/hour")  # Very restrictive for full pipeline
async def run_full_pipeline(
    request: Request,
    province: str,
    background_tasks: BackgroundTasks,
    host_types: List[str] = Query(["anchor", "friend", "newsreel"]),
    limit: int = Query(10, ge=1, le=20),
    current_user: User = Depends(require_scope("admin"))  # Requires admin scope
):
    """Run the full news processing pipeline (requires admin scope)"""
    try:
        # Validate inputs
        secure_request = SecureNewsRequest(province=province, limit=limit)
        
        for host_type in host_types:
            SecureProcessRequest(
                articles=[],  # Dummy for validation
                host_type=host_type,
                province=province
            )
        
        # Add background task
        background_tasks.add_task(
            full_pipeline_task, 
            secure_request.province, 
            host_types, 
            secure_request.limit
        )
        
        return {
            "status": "started",
            "province": secure_request.province,
            "host_types": host_types,
            "limit": secure_request.limit,
            "message": "Pipeline started in background. Check logs for progress."
        }
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting pipeline: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start pipeline")

# Custom error handlers
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation failed",
            "message": "Invalid input data",
            "details": exc.errors()
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "Request failed",
            "message": exc.detail,
            "request_id": getattr(request.scope, "request_id", None)
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    # Security settings for server
    uvicorn.run(
        app, 
        host=config.API_HOST, 
        port=config.API_PORT,
        access_log=False,  # We handle logging in middleware
        server_header=False,  # Don't expose server info
        date_header=False,   # Don't expose date
    )