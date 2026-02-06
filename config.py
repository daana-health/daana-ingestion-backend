"""
Configuration management for the Daana Ingestion Service
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # OpenAI Configuration
    openai_api_key: str
    
    # Application Configuration
    app_name: str = "Daana Ingestion Service"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Initialize settings
settings = Settings()
