# app/services/sec_scanner.py
import time
import threading
from app.utils.logger import setup_logger
from app.services.downloader import SecFilingDownloader
from app.core.config import TICKERS, FILING_TYPES, POLLING_INTERVAL
#=====================================================================================================================================================
logger = setup_logger(__name__)
#=====================================================================================================================================================
class SecFilingScanner:
    def __init__(self, polling_interval: int = POLLING_INTERVAL):
        self.polling_interval = polling_interval
        self.downloader = SecFilingDownloader()
        self._stop_event = threading.Event()
    
    def scan(self):
        logger.info("Starting SEC Filing Scanner...")
        while not self._stop_event.is_set():
            logger.info("Polling for new filings...")
            for ticker in TICKERS:
                for filing_type in FILING_TYPES:
                    self.downloader.download_filing(ticker, filing_type)
            logger.info(f"Sleeping for {self.polling_interval} seconds...")
            time.sleep(self.polling_interval)
    
    def start(self):
        self.thread = threading.Thread(target=self.scan, daemon=True)
        self.thread.start()
        logger.info("SEC Filing Scanner started in background thread.")
    
    def stop(self):
        self._stop_event.set()
        self.thread.join()
        logger.info("SEC Filing Scanner stopped.")

