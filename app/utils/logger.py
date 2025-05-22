# app/utils/logger.py
import logging
import sys
from app.core.config import LOG_LEVEL, LOG_FORMAT, LOG_DATE_FORMAT

def setup_logger(name: str) -> logging.Logger:
    """Set up a logger instance with consistent formatting."""
    logger = logging.getLogger(name)
    
    # Convert string log level to logging constant
    level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(level)

    # Only add handlers if none exist
    if not logger.handlers:
        # Console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(fmt=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
        )
        logger.addHandler(handler)

        # Optionally add file handler for persistent logs
        try:
            file_handler = logging.FileHandler('app.log')
            file_handler.setFormatter(
                logging.Formatter(fmt=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
            )
            logger.addHandler(file_handler)
        except Exception:
            # Don't fail if we can't create the log file
            pass

    return logger
