"""
Token service module.

This module provides JWT token generation, validation, refresh, and revocation.
"""
from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Set
import uuid
from app.config.settings import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

class TokenService:
    """Service for JWT token operations."""
    
    def __init__(self):
        """Initialize the token service with a revoked tokens store."""
        # In-memory store of revoked tokens
        # For production, use Redis or another distributed cache
        self._revoked_tokens: Set[str] = set()
    
    def generate_access_token(
        self,
        user_id: str,
        tenant_id: Optional[str] = None,
        role: Optional[str] = None,
        permissions: Optional[List[str]] = None,
        audience: str = "api",
    ) -> str:
        """
        Generate a JWT access token.
        
        Args:
            user_id: User identifier
            tenant_id: Optional tenant identifier
            role: Optional user role
            permissions: Optional list of permissions
            audience: Token audience (default: "api")
            
        Returns:
            JWT access token string
        """
        expires_delta = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        return self._generate_token(
            user_id=user_id,
            tenant_id=tenant_id,
            role=role,
            permissions=permissions,
            audience=audience,
            expires_delta=expires_delta,
            token_type="access"
        )
    
    def generate_refresh_token(
        self,
        user_id: str,
        tenant_id: Optional[str] = None,
    ) -> str:
        """
        Generate a JWT refresh token.
        
        Args:
            user_id: User identifier
            tenant_id: Optional tenant identifier
            
        Returns:
            JWT refresh token string
        """
        expires_delta = timedelta(minutes=settings.JWT_REFRESH_TOKEN_EXPIRE_MINUTES)
        return self._generate_token(
            user_id=user_id,
            tenant_id=tenant_id,
            audience="refresh",
            expires_delta=expires_delta,
            token_type="refresh"
        )
    
    def _generate_token(
        self,
        user_id: str,
        audience: str,
        expires_delta: timedelta,
        token_type: str,
        tenant_id: Optional[str] = None,
        role: Optional[str] = None,
        permissions: Optional[List[str]] = None,
    ) -> str:
        """
        Internal method to generate a JWT token.
        
        Args:
            user_id: User identifier
            audience: Token audience
            expires_delta: Token expiration time
            token_type: Token type (access or refresh)
            tenant_id: Optional tenant identifier
            role: Optional user role
            permissions: Optional list of permissions
            
        Returns:
            JWT token string
        """
        now = datetime.utcnow()
        
        # Generate a unique token ID (jti)
        token_id = str(uuid.uuid4())
        
        to_encode = {
            "sub": user_id,
            "iat": now,
            "exp": now + expires_delta,
            "jti": token_id,
            "type": token_type,
            "aud": audience
        }
        
        if tenant_id:
            to_encode["tenant_id"] = tenant_id
        
        if role:
            to_encode["role"] = role
            
        if permissions:
            to_encode["permissions"] = permissions
        
        try:
            return jwt.encode(
                to_encode, 
                settings.JWT_SECRET_KEY, 
                algorithm=settings.JWT_ALGORITHM
            )
        except Exception as e:
            logger.error(f"Error generating JWT token: {str(e)}")
            raise
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, str]:
        """
        Generate a new access token using a refresh token.
        
        Args:
            refresh_token: JWT refresh token
            
        Returns:
            Dictionary with new access and refresh tokens
            
        Raises:
            JWTError: If refresh token is invalid or expired
        """
        try:
            # Decode and validate the refresh token
            payload = self.decode_token(refresh_token)
            
            # Check if it's a refresh token
            if payload.get("type") != "refresh" or payload.get("aud") != "refresh":
                raise JWTError("Invalid token type")
            
            # Check if token has been revoked
            if payload.get("jti") in self._revoked_tokens:
                raise JWTError("Token has been revoked")
            
            # Extract user information
            user_id = payload.get("sub")
            tenant_id = payload.get("tenant_id")
            
            # Generate new tokens
            new_access_token = self.generate_access_token(
                user_id=user_id,
                tenant_id=tenant_id
            )
            
            new_refresh_token = self.generate_refresh_token(
                user_id=user_id,
                tenant_id=tenant_id
            )
            
            # Revoke the old refresh token
            self.revoke_token(refresh_token)
            
            return {
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer"
            }
            
        except JWTError as e:
            logger.error(f"Error refreshing token: {str(e)}")
            raise
    
    def decode_token(self, token: str) -> Dict[str, Any]:
        """
        Decode and validate a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload
            
        Raises:
            JWTError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token, 
                settings.JWT_SECRET_KEY, 
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            # Check if token has been revoked
            if payload.get("jti") in self._revoked_tokens:
                raise JWTError("Token has been revoked")
                
            return payload
        except JWTError as e:
            logger.error(f"JWT token validation failed: {str(e)}")
            raise
    
    def revoke_token(self, token: str) -> bool:
        """
        Revoke a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            True if token was revoked, False otherwise
        """
        try:
            # Decode the token without verification to extract the jti
            # This allows revoking tokens even if they're expired
            payload = jwt.decode(
                token, 
                settings.JWT_SECRET_KEY, 
                algorithms=[settings.JWT_ALGORITHM],
                options={"verify_exp": False}
            )
            
            # Add the token ID to the revoked tokens set
            token_id = payload.get("jti")
            if token_id:
                self._revoked_tokens.add(token_id)
                logger.info(f"Token revoked: {token_id}")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error revoking token: {str(e)}")
            return False