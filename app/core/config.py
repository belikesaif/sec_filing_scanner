# app/core/config.py
import os

# List of stock tickers to monitor
TICKERS = ["AAPL", "MSFT", "GOOG", "AMZN", "META"]

# Filing types to monitor
FILING_TYPES = ["10-K", "10-Q"]

# Polling frequency in seconds (e.g., every 3600 seconds = 1 hour)
POLLING_INTERVAL = 3600  # 1 hour

# Data storage paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Previously used for storing downloaded filings, but now we use the default SEC-EDGAR folder.
FILINGS_DIR = os.path.join(BASE_DIR, "sec-edgar-filings")

# SEC-EDGAR specific constants
ROOT_SAVE_FOLDER_NAME = "sec-edgar-filings"
FILING_FULL_SUBMISSION_FILENAME = "full-submission.txt"
PRIMARY_DOC_FILENAME_STEM = "primary-document"

# Email address for SEC EDGAR Downloader (required by sec-edgar-downloader)
SEC_EMAIL = "mohsinmahmood675@gmail.com"  

# Logging configuration
LOG_LEVEL = "INFO"
