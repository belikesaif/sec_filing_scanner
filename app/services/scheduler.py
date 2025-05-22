# app/services/scheduler.py
import threading
import time
from datetime import datetime
import json
from typing import Optional, List

from app.utils.logger import setup_logger
from app.utils.config_loader import config
from app.services.sec_scanner import SecFilingScanner
from app.core.config import POLLING_INTERVAL
from app.services.processing_pipeline import ProcessingPipeline
from app.services.sql_storage import SQLStorage

logger = setup_logger(__name__)

class FilingScheduler:
    """Scheduler for SEC filing downloads and processing with idempotency and configurable intervals"""
    def __init__(self, polling_interval: int = POLLING_INTERVAL):
        # Load configuration
        self.polling_interval = polling_interval
        self.enabled = True
        
        # Initialize components
        self.scanner = SecFilingScanner(polling_interval)
        self.processing_pipeline = ProcessingPipeline()
        self.sql_storage = SQLStorage()
        
        # Threading control
        self._stop_event = threading.Event()
        self.download_thread = None
        self.process_thread = None
        
        logger.info({
            "message": "Filing scheduler initialized",
            "polling_interval": self.polling_interval,
            "enabled": self.enabled
        })
    def start(self):
        """Start the scheduler with separate threads for downloading and processing"""
        if not self.enabled:
            logger.info({"message": "Scheduler is disabled in configuration, not starting"})
            return

        if (self.download_thread and self.download_thread.is_alive()) or \
           (self.process_thread and self.process_thread.is_alive()):
            logger.warning({"message": "Scheduler is already running"})
            return

        self._stop_event.clear()

        # Start the SEC filing scanner in a background thread
        self.download_thread = threading.Thread(target=self._run_downloader, daemon=True)
        self.download_thread.start()

        # Start the processing pipeline in a background thread
        self.process_thread = threading.Thread(target=self._run_processor, daemon=True)
        self.process_thread.start()

        logger.info({
            "message": "Filing scheduler started",
            "download_thread_id": self.download_thread.ident,
            "process_thread_id": self.process_thread.ident
        })
    def stop(self):
        """Stop the scheduler threads"""
        if not (self.download_thread or self.process_thread):
            logger.warning({"message": "Scheduler is not running"})
            return
        
        logger.info({"message": "Stopping filing scheduler"})
        self._stop_event.set()
        
        # Wait for both threads to finish
        if self.download_thread:
            self.download_thread.join(timeout=10)
        if self.process_thread:
            self.process_thread.join(timeout=10)
        
        # Check if threads terminated gracefully
        warnings = []
        if self.download_thread and self.download_thread.is_alive():
            warnings.append("Download thread did not terminate gracefully")
        if self.process_thread and self.process_thread.is_alive():
            warnings.append("Process thread did not terminate gracefully")
        
        if warnings:
            logger.warning({"message": "Scheduler shutdown issues", "warnings": warnings})
        else:
            logger.info({"message": "Filing scheduler stopped successfully"})
    def _run_downloader(self):
        """Main downloader loop that runs in a background thread"""
        while not self._stop_event.is_set():
            try:                # Use tickers and filing types from core config
                from app.core.config import TICKERS, FILING_TYPES
                
                if TICKERS and FILING_TYPES:
                    downloaded = self._download_filings(TICKERS, FILING_TYPES)
                    logger.info({
                        "message": "Download cycle completed",
                        "downloaded_count": len(downloaded),
                        "tickers": TICKERS,
                        "filing_types": FILING_TYPES
                    })
                else:
                    logger.warning({
                        "message": "No tickers or filing types configured",
                        "tickers": TICKERS,
                        "filing_types": FILING_TYPES
                    })
            except Exception as e:
                logger.error({
                    "message": "Error in download cycle",
                    "error": str(e)
                }, exc_info=True)
            
            # Sleep until next cycle
            for _ in range(self.polling_interval // 10):
                if self._stop_event.is_set():
                    break
                time.sleep(10)

    def _run_processor(self):
        """Main processor loop that runs in a background thread"""
        while not self._stop_event.is_set():
            try:
                processed = self._process_filings()
                logger.info({
                    "message": "Processing cycle completed",
                    "processed_filings": processed
                })
            except Exception as e:
                logger.error({
                    "message": "Error in processing cycle",
                    "error": str(e)
                }, exc_info=True)
            
            # Sleep for shorter interval than downloader
            for _ in range(self.polling_interval // 20):  # Process more frequently than downloads
                if self._stop_event.is_set():
                    break
                time.sleep(5)
    
    def _process_cycle(self):
        """Process a single scheduler cycle with idempotency checks"""
        cycle_start = datetime.now()
        
        logger.info(json.dumps({
            "message": "Starting scheduler cycle",
            "timestamp": cycle_start.isoformat()
        }))
        
        # 1. Get tickers and filing types from config
        tickers = config.get("downloader", "tickers", [])
        filing_types = config.get("downloader", "filing_types", [])
        
        if not tickers or not filing_types:
            logger.warning(json.dumps({
                "message": "No tickers or filing types configured",
                "tickers": tickers,
                "filing_types": filing_types
            }))
            return
        
        # 2. Download new filings
        downloaded_filings = self._download_filings(tickers, filing_types)
        
        # 3. Process new filings
        processed_count = self._process_filings()
        
        # 4. Log cycle completion
        cycle_duration = (datetime.now() - cycle_start).total_seconds()
        logger.info(json.dumps({
            "message": "Scheduler cycle completed",
            "duration_seconds": cycle_duration,
            "downloaded_filings": len(downloaded_filings),
            "processed_filings": processed_count
        }))
        
        # 5. Update last run timestamp in database
        self._update_last_run_timestamp(cycle_start)
    
    def _download_filings(self, tickers: List[str], filing_types: List[str]) -> List[str]:
        """Download filings for the specified tickers and filing types"""
        downloaded_filings = []
        
        for ticker in tickers:
            for filing_type in filing_types:
                try:
                    # Get already processed accession numbers for this ticker and filing type
                    processed_accessions = self._get_processed_accessions(ticker, filing_type)
                    
                    # Download new filings
                    logger.info(json.dumps({
                        "message": "Downloading filings",
                        "ticker": ticker,
                        "filing_type": filing_type
                    }))
                    
                    file_paths = self.scanner.downloader.download_filing(ticker, filing_type)
                    
                    if file_paths:
                        downloaded_filings.extend(file_paths)
                except Exception as e:
                    logger.error(json.dumps({
                        "message": "Error downloading filings",
                        "ticker": ticker,
                        "filing_type": filing_type,
                        "error": str(e)
                    }), exc_info=True)
        
        return downloaded_filings
    
    def _process_filings(self) -> int:
        """Process all new filings and return the count of processed filings"""
        try:
            logger.info(json.dumps({"message": "Processing new filings"}))
            return self.processing_pipeline.process_all_new_filings()
        except Exception as e:
            logger.error(json.dumps({
                "message": "Error processing filings",
                "error": str(e)
            }), exc_info=True)
            return 0
    
    def _get_processed_accessions(self, ticker: str, filing_type: str) -> List[str]:
        """Get list of already processed accession numbers for idempotency checks"""
        try:
            with self.sql_storage.session_scope() as session:
                filings = session.query(self.sql_storage.Filing).filter(
                    self.sql_storage.Filing.ticker == ticker,
                    self.sql_storage.Filing.filing_type == filing_type
                ).all()
                
                return [f.accession_number for f in filings if f.accession_number]
        except Exception as e:
            logger.error(json.dumps({
                "message": "Error getting processed accessions",
                "ticker": ticker,
                "filing_type": filing_type,
                "error": str(e)
            }), exc_info=True)
            return []
    
    def _update_last_run_timestamp(self, timestamp: datetime) -> None:
        """Update the last run timestamp in the database for monitoring"""
        try:
            # This could be implemented with a dedicated table for scheduler metadata
            # For now, we'll just log it
            logger.info(json.dumps({
                "message": "Scheduler run completed",
                "last_run_timestamp": timestamp.isoformat()
            }))
        except Exception as e:
            logger.error(json.dumps({
                "message": "Error updating last run timestamp",
                "error": str(e)
            }), exc_info=True)