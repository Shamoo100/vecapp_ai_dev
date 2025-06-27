"""
Authentication routes.

This module provides API routes for authentication.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from app.security.token_service import TokenService
from app.services.user_service import UserService
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])
token_service = TokenService()

class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    """Refresh token request model."""
    refresh_token: str

@router.post("/token", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate user and generate tokens.
    
    Args:
        form_data: OAuth2 password request form
        
    Returns:
        Access and refresh tokens
        
    Raises:
        HTTPException: If authentication fails
    """
    # Authenticate user
    user_service = UserService()
    user = await user_service.authenticate_user(
        email=form_data.username,
        password=form_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate tokens
    access_token = token_service.generate_access_token(
        user_id=str(user.id),
        tenant_id=str(user.tenant_id) if user.tenant_id else None,
        role=user.role,
        permissions=user.permissions
    )
    
    refresh_token = token_service.generate_refresh_token(
        user_id=str(user.id),
        tenant_id=str(user.tenant_id) if user.tenant_id else None
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshRequest):
    """
    Refresh access token using refresh token.
    
    Args:
        request: Refresh token request
        
    Returns:
        New access and refresh tokens
        
    Raises:
        HTTPException: If refresh token is invalid
    """
    try:
        tokens = token_service.refresh_access_token(request.refresh_token)
        return TokenResponse(**tokens)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid refresh token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/revoke", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_token(request: RefreshRequest):
    """
    Revoke a refresh token.
    
    Args:
        request: Refresh token request
        
    Returns:
        204 No Content
        
    Raises:
        HTTPException: If token revocation fails
    """
    success = token_service.revoke_token(request.refresh_token)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to revoke token"
        )