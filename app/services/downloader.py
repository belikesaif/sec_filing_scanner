# app/services/downloader.py
import os
from app.utils.logger import setup_logger
from sec_edgar_downloader import Downloader
from app.core.config import FILINGS_DIR, SEC_EMAIL
#=====================================================================================================================================================
logger = setup_logger(__name__)
#=====================================================================================================================================================
class SecFilingDownloader:
    def __init__(self, download_dir: str = FILINGS_DIR):
        self.download_dir = download_dir
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
        # Instantiate Downloader with required email and download directory
        self.downloader = Downloader(SEC_EMAIL, self.download_dir)

    def download_filing(self, ticker: str, filing_type: str):
        logger.info(f"Attempting to download {filing_type} for {ticker}...")
        try:
            # Download the filing; current version does not support limiting the number of filings
            file_paths = self.downloader.get(filing_type, ticker)
            logger.info(
                f"Downloaded {filing_type} for {ticker} successfully. Files: {file_paths}"
            )
            # Log a short sample from each downloaded file
            if file_paths and isinstance(file_paths, list):
                for file_path in file_paths:
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            sample = f.read(200)
                        logger.info(
                            f"Sample content from {file_path}:\n{sample}\n{'-'*60}"
                        )
                    except Exception as read_err:
                        logger.error(
                            f"Could not read file {file_path} for {ticker}: {read_err}"
                        )
        except Exception as e:
            logger.error(f"Error downloading {filing_type} for {ticker}: {e}")
