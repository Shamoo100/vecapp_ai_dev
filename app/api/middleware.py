"""
Middleware module for FastAPI with VecApp Central Authentication Support.

This module provides middleware components for the API including
CORS, rate limiting, and authentication context using central VecApp headers.
"""
from fastapi import FastAPI, Request, HTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
import logging
from typing import List
from app.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Initialize the rate limiter
limiter = Limiter(key_func=get_remote_address)

# Routes that don't require authentication
EXEMPT_PATHS = [
    "/health-check",
    "/docs",
    "/redoc", 
    "/openapi.json",
    "/auth/health"
]

def get_identifier(request: Request) -> str:
    """
    Get a unique identifier for the client for rate limiting.
    
    Args:
        request: The incoming request
            
    Returns:
        A unique identifier for the client
    """
    # Try to get user ID from X-auth-user header
    auth_user_header = request.headers.get("x-auth-user")
    if auth_user_header:
        try:
            import json
            user_data = json.loads(auth_user_header)
            user_id = user_data.get("id")
            if user_id:
                return f"user:{user_id}"
        except (json.JSONDecodeError, KeyError):
            pass
    
    # Try to get tenant ID from X-request-tenant header
    tenant_header = request.headers.get("x-request-tenant")
    if tenant_header:
        try:
            import json
            if tenant_header.startswith("{"):
                tenant_data = json.loads(tenant_header)
                tenant_id = tenant_data.get("id", tenant_data.get("tenant_id"))
                if tenant_id:
                    return f"tenant:{tenant_id}"
            else:
                return f"tenant:{tenant_header}"
        except (json.JSONDecodeError, KeyError):
            pass
    
    # Fall back to client IP
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    return request.client.host if request.client else "unknown"

class AuthContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to set up authentication context for requests using VecApp central auth.
    
    This middleware extracts user and tenant information from headers
    and makes them available to route handlers through request.state.
    """
    
    async def dispatch(self, request: Request, call_next):
        """Process the request and set up authentication context."""
        
        # Skip authentication for exempt paths
        if any(request.url.path.startswith(path) for path in EXEMPT_PATHS):
            return await call_next(request)
        
        # Extract user information from X-auth-user header
        auth_user_header = request.headers.get("x-auth-user")
        if auth_user_header:
            request.state.auth_user_header = auth_user_header
        
        # Extract tenant information from X-request-tenant header
        tenant_header = request.headers.get("x-request-tenant")
        if tenant_header:
            request.state.tenant_header = tenant_header
        
        # Continue with the request
        response = await call_next(request)
        return response

def setup_middleware(app: FastAPI) -> None:
    """
    Set up middleware for the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add authentication context middleware
    app.add_middleware(AuthContextMiddleware)
    
    # Register rate limit exceeded handler
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    logger.info("Middleware setup complete with VecApp central authentication support")