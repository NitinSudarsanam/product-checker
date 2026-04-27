import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime
from app.config import settings

# Ensure parent dir for LOG_FILE exists (robust in containers)
try:
    Path(settings.log_file).parent.mkdir(parents=True, exist_ok=True)
except Exception:
    # Fall back to a relative logs dir if env path is odd
    Path("logs").mkdir(parents=True, exist_ok=True)


def setup_logger(name: str = __name__) -> logging.Logger:
    """Set up logger with console and file handlers"""
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        settings.log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger


# Create default logger
logger = setup_logger("ubique")


async def log_to_database(db, event_type: str, details: dict, level: str = "INFO"):
    """Log event to database"""
    try:
        log_entry = {
            "event_type": event_type,
            "details": details,
            "level": level,
            "timestamp": datetime.utcnow()
        }
        await db.logs.insert_one(log_entry)
    except Exception as e:
        logger.error(f"Failed to log to database: {e}")
