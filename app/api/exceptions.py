"""
Exception handling module for FastAPI.

This module provides custom exception classes and handlers for the API.
"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

class AppException(Exception):
    """Base exception class for application-specific exceptions."""
    
    def __init__(
        self, 
        status_code: int, 
        detail: str, 
        headers: dict = None
    ):
        self.status_code = status_code
        self.detail = detail
        self.headers = headers

class DatabaseException(AppException):
    """Exception raised for database errors."""
    
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )

class AuthenticationException(AppException):
    """Exception raised for authentication errors."""
    
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )

class AuthorizationException(AppException):
    """Exception raised for authorization errors."""
    
    def __init__(self, detail: str = "Not authorized to perform this action"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )

class ResourceNotFoundException(AppException):
    """Exception raised when a requested resource is not found."""
    
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )

class ValidationException(AppException):
    """Exception raised for validation errors."""
    
    def __init__(self, detail: str = "Validation error"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )

def register_exception_handlers(app: FastAPI) -> None:
    """
    Register exception handlers with the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        """Handle application-specific exceptions."""
        logger.error(f"AppException: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=exc.headers
        )
    
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        """Handle unhandled exceptions."""
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected error occurred"}
        )