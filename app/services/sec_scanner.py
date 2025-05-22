# app/services/sec_scanner.py
import time
import threading
from datetime import datetime
from app.utils.logger import setup_logger
from app.services.downloader import SecFilingDownloader
from app.core.config import TICKERS, FILING_TYPES, POLLING_INTERVAL
from app.services.sql_storage import SQLStorage

#=====================================================================================================================================================
logger = setup_logger(__name__)
#=====================================================================================================================================================
class SecFilingScanner:
    def __init__(self, polling_interval: int = POLLING_INTERVAL):
        self.polling_interval = polling_interval
        self.downloader = SecFilingDownloader()
        self.storage = SQLStorage()
        self._stop_event = threading.Event()
        self._last_scan_time = {}  # Track last successful scan per ticker
        self._ticker_errors = {}  # Track consecutive errors per ticker
        
    def _should_scan(self, ticker: str) -> bool:
        """Determine if we should scan for a ticker based on last scan time."""
        now = datetime.now()
        last_scan = self._last_scan_time.get(ticker)
        
        # If never scanned or it's been at least polling_interval seconds
        if not last_scan or (now - last_scan).total_seconds() >= self.polling_interval:
            return True
        return False
        
    def scan(self):
        """Main scanning loop with error handling and retries."""
        logger.info("Starting SEC Filing Scanner...")
        max_retries = 3
        
        while not self._stop_event.is_set():
            try:
                for ticker in TICKERS:
                    if self._should_scan(ticker):
                        ticker_success = True
                        for filing_type in FILING_TYPES:
                            try:
                                self.downloader.download_filing(ticker, filing_type)
                                self._ticker_errors[ticker] = 0  # Reset on success
                            except Exception as e:
                                ticker_success = False
                                logger.error(f"Error scanning {filing_type} for {ticker}: {e}")
                                self._ticker_errors[ticker] = self._ticker_errors.get(ticker, 0) + 1
                                
                                if self._ticker_errors[ticker] >= max_retries:
                                    logger.error(f"Too many consecutive errors for {ticker}, will retry in {self.polling_interval * 2} seconds")
                                    time.sleep(5)  # Brief wait before next ticker
                                    continue
                                    
                        if ticker_success:
                            self._last_scan_time[ticker] = datetime.now()
                            logger.info(f"Successfully scanned all filings for {ticker}")
                
                # Sleep briefly between polling cycles
                logger.info(f"Completed scan cycle, sleeping for {self.polling_interval} seconds...")
                for _ in range(self.polling_interval // 10):  # Check stop event more frequently
                    if self._stop_event.is_set():
                        break
                    time.sleep(10)
                    
            except Exception as e:
                logger.error(f"Critical error in scanner: {e}")
                time.sleep(60)  # Brief wait after critical error
    
    def start(self):
        """Start the scanner in a background thread."""
        self.thread = threading.Thread(target=self.scan, daemon=True)
        self.thread.start()
        logger.info("SEC Filing Scanner started in background thread.")
    
    def stop(self):
        """Stop the scanner gracefully."""
        logger.info("Stopping SEC Filing Scanner...")
        self._stop_event.set()
        self.thread.join()
        logger.info("SEC Filing Scanner stopped.")

