import logging
import sys
import os
from dotenv import load_dotenv

load_dotenv()

def setup_logging(name: str, level: int = logging.INFO) -> logging.Logger:
    """Setup logger with consistent formatting"""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        
        # Enhanced formatter with component name
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.propagate = False  # Avoid duplicate logs
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with standard configuration"""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, log_level, logging.INFO)
    return setup_logging(name, level)