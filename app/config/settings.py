"""
Application settings module.

This module provides a centralized configuration system using Pydantic's BaseSettings.
It loads configuration from environment variables and .env files, with type validation
and documentation.
"""
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from functools import lru_cache
from typing import List, Optional, Union, Any
import json

class Settings(BaseSettings):
    """Application settings with validation and documentation."""
    
    # Database settings
    DATABASE_URL: str = Field(..., description="PostgreSQL connection string for database")
    DB_SCHEMA: str = Field("public", description="Database schema name")
    DB_MIN_CONNECTIONS: int = Field(5, description="Minimum number of connections in the pool")
    DB_MAX_CONNECTIONS: int = Field(20, description="Maximum number of connections in the pool")
    DB_COMMAND_TIMEOUT: float = Field(60.0, description="Command timeout in seconds")
    DB_MAX_INACTIVE_CONNECTION_LIFETIME: float = Field(300.0, description="Maximum lifetime of inactive connections in seconds")
    DB_USE_NULL_POOL: bool = Field(False, description="Whether to use NullPool for database connections")
    
    # Database connection details
    DB_HOST: str = Field("localhost", description="Database host")
    DB_PORT: int = Field(5432, description="Database port")
    DB_NAME: str = Field("vecap_ai", description="Database name")
    DB_USER: str = Field("postgres", description="Database user")
    DB_PASSWORD: str = Field("postgres", description="Database password")
    
    # JWT settings
    JWT_SECRET_KEY: str = Field(..., description="Secret key for JWT signing")
    JWT_ALGORITHM: str = Field("HS256", description="JWT signing algorithm")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, description="JWT access token expiration time in minutes")
    JWT_REFRESH_TOKEN_EXPIRE_MINUTES: int = Field(60 * 24 * 7, description="JWT refresh token expiration time in minutes")
    JWT_RESET_TOKEN_EXPIRE_HOURS: int = Field(48, description="JWT reset token expiration time in hours")
    
    # CORS settings
    CORS_ORIGINS: Union[List[str], str] = Field(default=["http://localhost:8000"], description="List of allowed origins for CORS")
    
    # API Key settings
    API_KEY_HEADER: str = Field("X-API-Key", description="Header name for API key authentication")
    
    # Server settings
    HOST: str = Field("localhost", description="Host to bind the server to")
    PORT: int = Field(3000, description="Port to bind the server to")
    
    # Secret key
    SECRET_KEY: str = Field("your_app_secret_key", description="Secret key for the application")
    
    # OpenAI API settings
    OPENAI_API_KEY: str = Field(..., description="API key for OpenAI")
    
    # Google API settings
    GEMINI_API_KEY: str = Field(..., description="API key for Google Gemini")
    
    # AWS Settings
    AWS_ACCESS_KEY_ID: Optional[str] = Field(None, description="AWS access key ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(None, description="AWS secret access key")
    AWS_REGION: Optional[str] = Field(None, description="AWS region")
    NEW_VISITOR_SIGNUP_QUEUE_URL: Optional[str] = Field(None, description="SQS queue URL for new visitor signup")
    #S3_BUCKET_NAME: Optional[str] = Field(None, description="AWS S3 bucket name")
    #SQS_QUEUE_URL: Optional[str] = Field(None, description="AWS SQS queue URL")
    #AWS_QUEUE_SERVICE_ENDPOINT: Optional[str] = Field(None, description="AWS SQS queue service endpoint")
    
    # Missing service URLs
    MEMBER_SERVICE_RESPONSE_QUEUE_URL: Optional[str] = Field(None, description="SQS queue URL for member service responses")
    FOLLOWUP_SERVICE_URL: Optional[str] = Field(None, description="URL for followup service")
    ANALYTICS_SERVICE_URL: Optional[str] = Field(None, description="URL for analytics service")
    
    # LangSmith settings
    LANGSMITH_API_KEY: Optional[str] = Field(None, description="API key for LangSmith")
    LANGSMITH_PROJECT: Optional[str] = Field(None, description="LangSmith project name")
    
    # Cache settings
    DEFAULT_CACHE_TTL: int = Field(300, description="Default cache TTL in seconds")
    
    # Sentry settings
    SENTRY_DSN: Optional[str] = Field(None, description="Sentry DSN for error tracking")
    
    # External Database URLs
    MEMBER_SERVICE_DATABASE_URL: Optional[str] = Field(None, description="PostgreSQL connection string for Member Service")
    CALENDAR_SERVICE_DATABASE_URL: Optional[str] = Field(None, description="PostgreSQL connection string for Calendar Service")
    CONNECT_SERVICE_MONGODB_URL: Optional[str] = Field(None, description="MongoDB connection string for Connect Service")
    AUTH_SERVICE_DATABASE_URL: Optional[str] = Field(None, description="PostgreSQL connection string for Auth Service")
    
    # Pydantic v2 configuration
    model_config = {
        "extra": "allow",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "from_attributes": True,
        "case_sensitive": False
    }
    
    @field_validator("CORS_ORIGINS", mode="before")
    def parse_cors_origins(cls, v: Any) -> List[str]:
        """Parse CORS_ORIGINS from various input formats."""
        if isinstance(v, str) and v:
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                if "," in v:
                    return [origin.strip() for origin in v.split(",") if origin.strip()]
                return [v.strip()]
        elif isinstance(v, str) and not v:
            return []
        return v
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Return the CORS origins list."""
        return self.CORS_ORIGINS

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

# Global settings instance for backward compatibility
settings = get_settings()
