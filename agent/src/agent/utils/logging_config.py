import logging
import sys
from dotenv import load_dotenv
load_dotenv()

def setup_logging(name: str = "app", level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.propagate = False  # Avoid duplicate logs if root logger has handlers
    return logger


import os
def get_logger(name: str = "app") -> logging.Logger:
    logger = setup_logging("router", level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO))
    return logger