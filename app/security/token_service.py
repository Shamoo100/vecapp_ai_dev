from jose import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from uuid import UUID
from app.config.settings import get_settings

settings = get_settings()

class TokenService:
    """Service for generating and validating JWT tokens"""
    
    def generate_token(
        self,
        user_id: str,
        tenant_id: Optional[str] = None,
        role: Optional[str] = None,
        permissions: Optional[list] = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Generate a JWT token for a user"""
        to_encode = {"sub": user_id}
        
        if tenant_id:
            to_encode["tenant_id"] = tenant_id
        
        if role:
            to_encode["role"] = role
            
        if permissions:
            to_encode["permissions"] = permissions
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=30)
            
        to_encode.update({"exp": expire})
        
        return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    def generate_system_token(self, tenant_id: UUID) -> str:
        """Generate a system token for inter-service communication"""
        return self.generate_token(
            user_id="system",
            tenant_id=str(tenant_id),
            role="system",
            permissions=["*"],
            expires_delta=timedelta(minutes=5)
        )
    
    def decode_token(self, token: str) -> Dict[str, Any]:
        """Decode and validate a JWT token"""
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]) 