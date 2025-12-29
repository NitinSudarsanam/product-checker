from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path
from pydantic import field_validator

# Get the project root directory (two levels up from this file)
PROJECT_ROOT = Path(__file__).parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    # MongoDB Configuration
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_database: str = "ubique_product_checker"
    
    # Backend Configuration
    backend_host: str = "0.0.0.0"
    backend_port: int = 8080
    backend_reload: bool = True
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    
    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    # Scraper Configuration
    scraper_timeout: int = 30
    scraper_user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    scraper_max_concurrent: int = 5
    scraper_use_playwright: bool = True
    scraper_headless: bool = False  # False = visible browser (better bot evasion)
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    
    # Frontend (not used by backend but in .env)
    next_public_api_url: str = "http://localhost:8080"
    
    # Email (future feature, not used yet but in .env)
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    notification_email: str = ""
    
    class Config:
        env_file = str(ENV_FILE)
        case_sensitive = False


settings = Settings()

# Debug: Log the loaded settings
import logging
logger = logging.getLogger(__name__)
logger.info(f"Config loaded from: {ENV_FILE}")
logger.info(f"SCRAPER_HEADLESS setting: {settings.scraper_headless}")
