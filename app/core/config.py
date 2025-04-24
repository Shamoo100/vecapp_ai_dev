from pydantic import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # Kafka
    KAFKA_SERVERS: List[str]
    
    # OpenAI
    OPENAI_API_KEY: str
    
    # Tenant
    DEFAULT_TENANT_SCHEMA: str = "public"
    
    # Security
    SECRET_KEY: str
    API_KEY_HEADER: str = "X-API-Key"
    
    # Monitoring
    PROMETHEUS_PORT: int = 9090
    GRAFANA_PORT: int = 3000
    
    # Email
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str
    
    # Redis
    REDIS_URL: str
    
    class Config:
        env_file = ".env"

settings = Settings() 