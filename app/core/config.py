# app/core/config.py
import os
from typing import List
import logging

# Logging configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

# Load YAML config
import yaml
with open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config.yaml'), 'r') as f:
    yaml_config = yaml.safe_load(f)

# List of stock tickers to monitor - loaded from config or use defaults
try:
    TICKERS = yaml_config['downloader']['tickers']
except:
    TICKERS = ["AAPL", "MSFT", "GOOG", "AMZN", "META"]

# Filing types to monitor - loaded from config or use defaults
try:
    FILING_TYPES = yaml_config['downloader']['filing_types']
except:
    FILING_TYPES = ["10-K", "10-Q"]

# SEC email address from config
try:
    SEC_EMAIL = yaml_config['downloader']['sec_email']
except:
    SEC_EMAIL = os.getenv('SEC_EMAIL', 'your-email@domain.com')

# Polling frequency in seconds (from config or default 10 minutes)
try:
    POLLING_INTERVAL = yaml_config['scheduler']['polling_interval']
except:
    POLLING_INTERVAL = 600

# Data storage paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) 
FILINGS_DIR = os.path.join(BASE_DIR, "sec-edgar-filings")

# Database configuration
DB_DIR = os.path.join(BASE_DIR, "data", "db")
DB_PATH = os.path.join(DB_DIR, "sec_filings.db")
DB_URL = f"sqlite:///{DB_PATH}"

# SEC-EDGAR specific constants
ROOT_SAVE_FOLDER_NAME = "sec-edgar-filings"
FILING_FULL_SUBMISSION_FILENAME = "full-submission.txt"
PRIMARY_DOC_FILENAME_STEM = "primary-document"

# Email address for SEC EDGAR Downloader 
SEC_EMAIL = os.getenv('SEC_EMAIL', 'your-email@domain.com')
