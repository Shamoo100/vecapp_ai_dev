from pydantic_settings import BaseSettings
from typing import List, Dict, Any, Optional
import os
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings"""
    # API and App settings
    APP_NAME: str = "vecapp-ai"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["*"]
    
    # Auth settings
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    
    # Database settings
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    POSTGRES_DB: str
    
    @property
    def DATABASE_URL(self) -> str:
        """Get the database connection URL"""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # Redis settings
    REDIS_HOST: str
    REDIS_PORT: str
    REDIS_PASSWORD: Optional[str] = None
    
    @property
    def REDIS_URL(self) -> str:
        """Get the Redis connection URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/0"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"
    
    # AWS settings
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    S3_BUCKET_NAME: str
    SQS_QUEUE_URL: str
    SNS_TOPIC_ARN: str
    
    # LangChain settings
    OPENAI_API_KEY: str
    LANGCHAIN_API_KEY: str
    LANGCHAIN_PROJECT: str = "vecapp-followup-summary"
    LANGSMITH_API_KEY: str
    LANGSMITH_PROJECT: str = "vecapp-followup-summary"
    
    # External service endpoints
    FOLLOWUP_SERVICE_URL: str
    ANALYTICS_SERVICE_URL: str
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings() 