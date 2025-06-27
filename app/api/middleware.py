"""Middleware module for FastAPI.

This module provides middleware components for the API.
"""
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
import logging
from app.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Initialize the rate limiter
limiter = Limiter(key_func=get_remote_address)

# Custom key function that can use API key if available
def get_identifier(request):
    """
    Get a unique identifier for the client.
    
    Args:
        request: The incoming request
            
    Returns:
        A unique identifier for the client
    """
    # Try to get API key from header
    api_key = request.headers.get(settings.API_KEY_HEADER)
    if api_key:
        return f"api_key:{api_key}"
    
    # Fall back to client IP
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    return request.client.host

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
    
    # Register rate limit exceeded handler
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    logger.info("Middleware setup complete with slowapi rate limiting")