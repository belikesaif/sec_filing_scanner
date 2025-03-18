# app/utils/logger.py
import logging
from app.core.config import LOG_LEVEL

def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)
    
    if not logger.handlers:
        # Create console handler
        ch = logging.StreamHandler()
        ch.setLevel(LOG_LEVEL)
        # Create formatter and add it to the handler
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        # Add handler to logger
        logger.addHandler(ch)
    
    return logger
