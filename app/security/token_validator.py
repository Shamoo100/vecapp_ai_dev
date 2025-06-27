"""
Authentication module.

This module provides authentication utilities for the API.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from typing import Dict, Optional
from app.security.token_service import TokenService
import logging

logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")
token_service = TokenService()

async def verify_token(token: str = Depends(oauth2_scheme)) -> Dict:
    """
    Verify JWT token and extract user information.
    
    Args:
        token: JWT token from Authorization header
        
    Returns:
        Dictionary with user information
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode and validate the token
        payload = token_service.decode_token(token)
        
        # Check if it's an access token
        if payload.get("type") != "access":
            raise JWTError("Invalid token type")
        
        # Extract user information
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        # Extract additional user data from token
        user_data = {
            "id": user_id,
            "tenant_id": payload.get("tenant_id"),
            "role": payload.get("role"),
            "permissions": payload.get("permissions", [])
        }
        
        return user_data
    except JWTError as e:
        logger.error(f"Token verification failed: {str(e)}")
        raise credentials_exception

async def verify_tenant_access(
    user_data: Dict = Depends(verify_token),
    tenant_id: Optional[str] = None
) -> Dict:
    """
    Verify user has access to the specified tenant.
    
    Args:
        user_data: User data from token
        tenant_id: Optional tenant ID to check access for
        
    Returns:
        User data if access is allowed
        
    Raises:
        HTTPException: If user doesn't have access to the tenant
    """
    # If no tenant_id is specified, return user data
    if not tenant_id:
        return user_data
    
    # Check if user has access to the tenant
    user_tenant_id = user_data.get("tenant_id")
    
    # Allow access if user's tenant matches requested tenant
    # or if user has no tenant restriction
    if not user_tenant_id or user_tenant_id == tenant_id:
        return user_data
    
    # Deny access if user's tenant doesn't match requested tenant
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authorized to access this tenant"
    )