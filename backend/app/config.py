"""
Application configuration using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "AI-Agent ERP"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://erp_user:erp_password@localhost:5432/ai_erp"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 40
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # AWS
    AWS_REGION: str = "eu-north-1"  # Stockholm/Oslo
    AWS_TEXTRACT_REGION: str = "eu-west-1"  # Ireland (Textract not available in Stockholm)
    AWS_ACCESS_KEY: str = ""
    AWS_SECRET_KEY: str = ""
    S3_BUCKET_DOCUMENTS: str = "ai-erp-documents"
    
    # Anthropic Claude API
    ANTHROPIC_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"
    CLAUDE_MAX_TOKENS: int = 4096
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3002",
        "http://localhost:3003",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3002",
        "http://127.0.0.1:3003",
    ]
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # Agent Settings
    DEFAULT_CONFIDENCE_THRESHOLD: int = 85
    AUTO_BOOK_ENABLED: bool = True
    
    # Demo Environment Settings
    ENVIRONMENT: str = "production"  # production/demo/development
    DEMO_MODE_ENABLED: bool = False
    DEMO_TENANT_ID: str = ""  # UUID of demo tenant
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # DNB Open Banking
    DNB_CLIENT_ID: str = ""
    DNB_CLIENT_SECRET: str = ""
    DNB_API_KEY: str = ""
    DNB_REDIRECT_URI: str = "http://localhost:8000/api/dnb/oauth/callback"
    DNB_USE_SANDBOX: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()
