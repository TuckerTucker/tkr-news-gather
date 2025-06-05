"""
Security middleware for TKR News Gather
Implements security headers, error handling, and request logging
"""

import time
import uuid
from typing import Callable, Dict, Any
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
import starlette.status as status

from .logger import get_logger
from .config import Config

logger = get_logger(__name__)

class SecurityHeadersMiddleware:
    """Middleware to add security headers to all responses"""
    
    def __init__(self, app, config: Config):
        self.app = app
        self.config = config
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start" and self.config.ENABLE_SECURITY_HEADERS:
                headers = dict(message.get("headers", []))
                
                # Security headers
                security_headers = {
                    b"x-content-type-options": b"nosniff",
                    b"x-frame-options": b"DENY",
                    b"x-xss-protection": b"1; mode=block",
                    b"strict-transport-security": b"max-age=31536000; includeSubDomains",
                    b"referrer-policy": b"strict-origin-when-cross-origin",
                    b"permissions-policy": b"camera=(), microphone=(), geolocation=()",
                    b"content-security-policy": b"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
                }
                
                headers.update(security_headers)
                message["headers"] = list(headers.items())
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)

class RequestLoggingMiddleware:
    """Middleware for security-focused request logging"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        request = Request(scope, receive)
        
        # Log request details (excluding sensitive data)
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        method = request.method
        path = request.url.path
        
        logger.info(
            f"Request started",
            extra={
                "request_id": request_id,
                "client_ip": client_ip,
                "method": method,
                "path": path,
                "user_agent": user_agent[:100],  # Limit length
            }
        )
        
        # Add request ID to scope for other middleware/handlers
        scope["request_id"] = request_id
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_code = message["status"]
                process_time = time.time() - start_time
                
                # Log response details
                log_level = "warning" if status_code >= 400 else "info"
                logger.log(
                    getattr(logger, log_level.upper()),
                    f"Request completed",
                    extra={
                        "request_id": request_id,
                        "status_code": status_code,
                        "process_time": round(process_time, 3),
                        "client_ip": client_ip,
                        "method": method,
                        "path": path,
                    }
                )
                
                # Add request ID header
                headers = dict(message.get("headers", []))
                headers[b"x-request-id"] = request_id.encode()
                message["headers"] = list(headers.items())
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)

class ErrorHandlingMiddleware:
    """Middleware for secure error handling"""
    
    def __init__(self, app, config: Config):
        self.app = app
        self.config = config
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        try:
            await self.app(scope, receive, send)
        except Exception as exc:
            request = Request(scope, receive)
            response = await self.handle_exception(request, exc)
            await response(scope, receive, send)
    
    async def handle_exception(self, request: Request, exc: Exception) -> Response:
        """Handle exceptions securely"""
        request_id = getattr(request.scope, "request_id", "unknown")
        client_ip = request.client.host if request.client else "unknown"
        
        # Log the full error details securely
        logger.error(
            f"Unhandled exception: {type(exc).__name__}",
            extra={
                "request_id": request_id,
                "client_ip": client_ip,
                "path": request.url.path,
                "method": request.method,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            },
            exc_info=True
        )
        
        # Return sanitized error response
        if isinstance(exc, HTTPException):
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": "Request failed",
                    "message": exc.detail if not self._is_sensitive_error(exc) else "An error occurred",
                    "request_id": request_id,
                }
            )
        
        # For unexpected errors, don't expose internal details
        error_message = "Internal server error" if not self.config.DEBUG else str(exc)
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "message": error_message,
                "request_id": request_id,
            }
        )
    
    def _is_sensitive_error(self, exc: HTTPException) -> bool:
        """Check if error contains sensitive information"""
        sensitive_keywords = [
            "database", "connection", "auth", "token", "key", "password",
            "secret", "credential", "internal", "config"
        ]
        
        detail = str(exc.detail).lower()
        return any(keyword in detail for keyword in sensitive_keywords)

def create_trusted_host_middleware():
    """Create middleware to validate trusted hosts"""
    from fastapi.middleware.trustedhost import TrustedHostMiddleware
    
    # Allow localhost for development, configure for production
    allowed_hosts = ["localhost", "127.0.0.1", "*.yourdomain.com"]
    
    return TrustedHostMiddleware(allowed_hosts=allowed_hosts)

def create_https_redirect_middleware():
    """Create middleware to redirect HTTP to HTTPS in production"""
    from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
    
    return HTTPSRedirectMiddleware

class RateLimitingMiddleware:
    """Simple rate limiting middleware"""
    
    def __init__(self, app, config: Config):
        self.app = app
        self.config = config
        self.client_requests: Dict[str, list] = {}
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        client_ip = request.client.host if request.client else "unknown"
        
        # Simple in-memory rate limiting (use Redis in production)
        current_time = time.time()
        minute_ago = current_time - 60
        
        # Clean old requests
        if client_ip in self.client_requests:
            self.client_requests[client_ip] = [
                req_time for req_time in self.client_requests[client_ip] 
                if req_time > minute_ago
            ]
        else:
            self.client_requests[client_ip] = []
        
        # Check rate limit
        if len(self.client_requests[client_ip]) >= self.config.RATE_LIMIT_PER_MINUTE:
            response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {self.config.RATE_LIMIT_PER_MINUTE} requests per minute allowed",
                    "retry_after": 60
                }
            )
            await response(scope, receive, send)
            return
        
        # Add current request
        self.client_requests[client_ip].append(current_time)
        
        await self.app(scope, receive, send)

class HealthCheckMiddleware:
    """Middleware for health check endpoints"""
    
    def __init__(self, app):
        self.app = app
        self.start_time = time.time()
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # Handle health check
            if request.url.path == "/health":
                uptime = time.time() - self.start_time
                health_data = {
                    "status": "healthy",
                    "uptime": round(uptime, 2),
                    "timestamp": time.time(),
                    "version": "0.1.0"
                }
                
                response = JSONResponse(content=health_data)
                await response(scope, receive, send)
                return
        
        await self.app(scope, receive, send)