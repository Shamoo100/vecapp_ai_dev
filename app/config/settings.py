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
import os
import json
print("Environment variables:", {k: v for k, v in os.environ.items() if not k.startswith('_')})

class Settings(BaseSettings):
    """
    Application settings with validation and documentation.
    
    This class defines all configuration parameters for the application,
    with appropriate types, default values, and documentation.
    Environment variables take precedence over defaults.
    """
    
    # Database settings
    DATABASE_URL: str = Field(
        ..., 
        description="PostgreSQL connection string for database"
    )
    DB_MIN_CONNECTIONS: int = Field(
        5, 
        description="Minimum number of connections in the pool"
    )
    DB_MAX_CONNECTIONS: int = Field(
        20, 
        description="Maximum number of connections in the pool"
    )
    DB_COMMAND_TIMEOUT: float = Field(
        60.0, 
        description="Command timeout in seconds"
    )
    DB_MAX_INACTIVE_CONNECTION_LIFETIME: float = Field(
        300.0, 
        description="Maximum lifetime of inactive connections in seconds"
    )
    DB_USE_NULL_POOL: bool = Field(
        False,
        description="Whether to use NullPool for database connections (useful for testing)"
    )
    
    # JWT settings
    JWT_SECRET_KEY: str = Field(
        ...,
        description="Secret key for JWT signing"
    )
    JWT_ALGORITHM: str = Field(
        "HS256",
        description="JWT signing algorithm"
    )
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        30,
        description="JWT access token expiration time in minutes"
    )
    JWT_REFRESH_TOKEN_EXPIRE_MINUTES: int = Field(
        60 * 24 * 7,  # 7 days
        description="JWT refresh token expiration time in minutes"
    )
    JWT_RESET_TOKEN_EXPIRE_HOURS: int = Field(
        48,
        description="JWT reset token expiration time in hours"
    )
    
    # CORS settings
    CORS_ORIGINS: Union[List[str], str] = Field(
        default=["http://localhost:8000"],
        description="List of allowed origins for CORS"
    )
    
    # API Key settings
    API_KEY_HEADER: str = Field(
        "X-API-Key",
        description="Header name for API key authentication"
    )
    
    # Server settings
    HOST: str = Field(
        "localhost",
        description="Host to bind the server to"
    )
    PORT: int = Field(
        3000,
        description="Port to bind the server to"
    )
    
    # Database connection details
    DB_HOST: str = Field(
        "localhost",
        description="Database host"
    )
    DB_PORT: int = Field(
        5432,
        description="Database port"
    )
    DB_NAME: str = Field(
        "vecap_ai",
        description="Database name"
    )
    DB_USER: str = Field(
        "postgres",
        description="Database user"
    )
    DB_PASSWORD: str = Field(
        "postgres",
        description="Database password"
    )
    
    # Secret key
    SECRET_KEY: str = Field(
        "your_app_secret_key",
        description="Secret key for the application"
    )
    
    # OpenAI API settings
    OPENAI_API_KEY: str = Field(
        ...,
        description="API key for OpenAI"
    )

    # AWS Settings
    AWS_ACCESS_KEY_ID: Optional[str] = Field(
        None,
        description="AWS access key ID"
    )
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(
        None,
        description="AWS secret access key" 
    )
    AWS_REGION: Optional[str] = Field(
        None,
        description="AWS region"
    )
    S3_BUCKET_NAME: Optional[str] = Field(
        None,
        description="AWS S3 bucket name"
    )
    SQS_QUEUE_URL: Optional[str] = Field(
       None,
        description="AWS SQS queue URL"
    )
    
    # Sentry settings
    SENTRY_DSN: Optional[str] = Field(
        None,
        description="Sentry DSN for error tracking"
    )
    
    # Pydantic v2 configuration
    model_config = {
        "extra": "allow",  # This allows extra fields from env vars
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "from_attributes": True,  # Updated from orm_mode in Pydantic v2
        "case_sensitive": False  # Allow case-insensitive env vars
    }

    @field_validator("CORS_ORIGINS", mode="before")
    def parse_cors_origins(cls, v: Any) -> List[str]:
        """
        Parse CORS_ORIGINS from various input formats.
        
        This validator handles different input formats for CORS_ORIGINS:
        - List of strings
        - Comma-separated string
        - Single URL string
        - Empty string
        
        Returns:
            List of CORS origins
        """
        if isinstance(v, str) and v:
            try:
                # Try to parse as JSON
                return json.loads(v)
            except json.JSONDecodeError:
                # If not valid JSON, treat as comma-separated string
                if "," in v:
                    return [origin.strip() for origin in v.split(",") if origin.strip()]
                # Single URL
                return [v.strip()]
        elif isinstance(v, str) and not v:
            # Empty string case
            return []
        return v

    @property
    def cors_origins_list(self) -> List[str]:
        """
        Return the CORS origins list.
        
        Since we now handle parsing in the validator, this property
        simply returns the already-parsed CORS_ORIGINS value.
        
        Returns:
            List of CORS origins
        """
        return self.CORS_ORIGINS

# Create a global settings instance for direct imports
settings = Settings()
print("CORS_ORIGINS:", settings.cors_origins_list)

@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    This function returns a cached instance of the Settings class,
    which improves performance by avoiding re-parsing environment
    variables on each call.
    
    Returns:
        Settings: Application settings instance
    """
    return Settings()