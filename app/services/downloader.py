# app/services/downloader.py
from typing import List, Dict
from datetime import datetime
from app.utils.logger import setup_logger
from sec_edgar_downloader import Downloader
from app.core.config import FILINGS_DIR, SEC_EMAIL
from app.services.sql_storage import SQLStorage
import os

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
        # Initialize SQL storage
        self.storage = SQLStorage()
        self.download_stats = {}  # Track stats per ticker

    def extract_accession_number(self, file_path: str) -> str:
        """Extract accession number from filing path."""
        # Format is: sec-edgar-filings/TICKER/TYPE/ACCESSION/full-submission.txt
        parts = file_path.split(os.sep)
        if len(parts) >= 4:
            return parts[-2]  # Accession number is second to last part
        return ""
        
    def download_filing(self, ticker: str, filing_type: str) -> List[str]:
        """Download SEC filing while avoiding duplicates. Returns list of downloaded file paths."""
        if ticker not in self.download_stats:
            self.download_stats[ticker] = {
                'attempted': 0, 
                'downloaded': 0, 
                'skipped': 0, 
                'errors': 0,
                'last_error': None,
                'last_success': None
            }
            
        self.download_stats[ticker]['attempted'] += 1
        logger.info(f"Attempting to download {filing_type} for {ticker}... (Stats: {self.download_stats[ticker]})")
        
        downloaded_files = []
        try:
            # Check latest filing dates to optimize download
            with self.storage.session_scope() as session:
                latest = session.query(self.storage.Filing).filter(
                    self.storage.Filing.ticker == ticker,
                    self.storage.Filing.filing_type == filing_type
                ).order_by(self.storage.Filing.filing_date.desc()).first()
            
            # Download the filing
            file_paths = self.downloader.get(filing_type, ticker, after=latest.filing_date if latest else None)
            
            if not file_paths or not isinstance(file_paths, list):
                logger.warning(f"No new filings found for {ticker} ({filing_type})")
                return downloaded_files

            # Process each downloaded file
            for file_path in file_paths:
                try:
                    # Extract accession number
                    accession_number = self.extract_accession_number(file_path)
                    if not accession_number:
                        logger.warning(f"Could not extract accession number from {file_path}")
                        continue

                    # Check if this filing was already processed
                    if self.storage.get_filing_by_accession(accession_number):
                        logger.info(f"Filing {accession_number} already processed, skipping")
                        self.download_stats[ticker]['skipped'] += 1
                        continue

                    self.download_stats[ticker]['downloaded'] += 1
                    self.download_stats[ticker]['last_success'] = datetime.now().isoformat()
                    downloaded_files.append(file_path)
                    logger.info(f"Successfully downloaded filing for {ticker} (Stats: {self.download_stats[ticker]})")

                except Exception as read_err:
                    logger.error(f"Could not process file {file_path} for {ticker}: {read_err}")
                    self.download_stats[ticker]['errors'] += 1
                    self.download_stats[ticker]['last_error'] = str(read_err)

        except Exception as e:
            logger.error(f"Error downloading {filing_type} for {ticker}: {e}")
            self.download_stats[ticker]['errors'] += 1
            self.download_stats[ticker]['last_error'] = str(e)
            
        return downloaded_files
    
    def get_download_stats(self) -> Dict[str, Dict]:
        """Get download statistics for all tickers."""
        return self.download_stats
