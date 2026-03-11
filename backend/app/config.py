import logging
from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path
from pydantic import field_validator

PROJECT_ROOT = Path(__file__).parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
_PLACEHOLDER_KEY = "your-secret-key-change-in-production"


class Settings(BaseSettings):
    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_database: str = "ubique_product_checker"
    mongodb_max_pool_size: int = 20

    # Backend
    backend_host: str = "0.0.0.0"
    backend_port: int = 8080
    backend_reload: bool = False

    # Security
    secret_key: str = _PLACEHOLDER_KEY
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:3001"]

    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            v = v.strip()
            if v.startswith('['):
                import json
                return [o.strip() for o in json.loads(v)]
            return [o.strip().strip('"\'') for o in v.split(',') if o.strip()]
        return v

    # Scraper
    scraper_timeout: int = 30
    scraper_user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    scraper_max_concurrent: int = 5
    scraper_use_playwright: bool = True
    scraper_headless: bool = True
    scraper_check_variants: bool = True  # Click variant options and check each
    scrapingbee_api_key: str = ""
    scrapingbee_country_code: str = "us"

    # Logging — resolved to absolute path at load time (8.4)
    log_level: str = "INFO"
    log_file: str = "logs/app.log"

    @field_validator('log_file', mode='before')
    @classmethod
    def make_log_path_absolute(cls, v):
        p = Path(v)
        if not p.is_absolute():
            return str(PROJECT_ROOT / p)
        return v

    # Frontend env (used by frontend build, not backend)
    next_public_api_url: str = "http://localhost:8080"

    # Email (future)
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    notification_email: str = ""

    model_config = {
        "env_file": str(ENV_FILE),
        "case_sensitive": False,
        "extra": "ignore",  # ignore unknown .env keys (8.6)
    }


settings = Settings()

_log = logging.getLogger(__name__)
_log.info(f"Config loaded from {ENV_FILE}")

if settings.secret_key == _PLACEHOLDER_KEY:
    _log.warning("SECRET_KEY is the default placeholder — change it before deploying to production")

if settings.backend_reload:
    _log.warning("BACKEND_RELOAD=true — background scan tasks will be killed on file changes")
