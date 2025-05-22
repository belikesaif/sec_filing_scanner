import os
from datetime import datetime
from typing import Dict, List, Optional
from app.utils.logger import setup_logger
from app.core.config import FILINGS_DIR, FILING_FULL_SUBMISSION_FILENAME
from app.services.processor import FilingProcessor
from app.services.sql_storage import SQLStorage
from app.services.embedding import EmbeddingService

logger = setup_logger(__name__)

class ProcessingPipeline:
    def __init__(self):
        self.storage = SQLStorage()
        self.processor = FilingProcessor()
        self.embedding_service = EmbeddingService()
        self.processing_stats = {}  # Track stats per ticker
        
    def _update_stats(self, ticker: str, status: str):
        if ticker not in self.processing_stats:
            self.processing_stats[ticker] = {'processed': 0, 'skipped': 0, 'errors': 0}
        self.processing_stats[ticker][status] += 1
        
    def _extract_filing_info(self, file_path: str) -> Dict:
        """Extract filing information from the file path."""
        parts = os.path.normpath(file_path).split(os.sep)
        try:
            filings_index = parts.index(os.path.basename(FILINGS_DIR))
            return {
                'ticker': parts[filings_index + 1],
                'filing_type': parts[filings_index + 2],
                'accession_number': parts[filings_index + 3]
            }
        except Exception as e:
            logger.error(f"Error parsing path {file_path}: {e}")
            return {}    
            
    def process_filing(self, file_path: str) -> bool:
        """Process a single filing and store its data."""
        try:
            # Extract filing information
            filing_info = self._extract_filing_info(file_path)
            if not filing_info:
                logger.error(f"Could not extract filing info from {file_path}")
                return False
                
            ticker = filing_info['ticker']
            logger.info(f"Processing filing for {ticker}... (Stats: {self.processing_stats.get(ticker, {})})")

            # Check if already processed
            if self.storage.get_filing_by_accession(filing_info['accession_number']):
                logger.info(f"Filing {filing_info['accession_number']} already processed")
                self._update_stats(ticker, 'skipped')
                return True

            # Load and process the filing
            processor = FilingProcessor()
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract filing date and metrics
            filing_date = processor.extract_filing_date(content)
            metrics = processor.process(content)
            
            if not metrics:
                logger.error(f"No metrics extracted from filing {filing_info['accession_number']} for {ticker}")
                self._update_stats(ticker, 'errors')
                return False

            # Store filing in database
            filing_id = self.storage.insert_filing(
                ticker=ticker,
                filing_type=filing_info['filing_type'],
                filing_date=filing_date,
                file_path=file_path,
                full_text=content,
                accession_number=filing_info['accession_number']
            )

            if filing_id == -1:
                logger.error(f"Failed to insert filing {filing_info['accession_number']} for {ticker}")
                self._update_stats(ticker, 'errors')
                return False

            # Store metrics
            if metrics:
                self.storage.insert_metrics(filing_id, metrics)

            # Generate and store embeddings
            self.embedding_service.process_filing(filing_id, content)

            logger.info(f"Successfully processed filing {filing_info['accession_number']} for {ticker}")
            self._update_stats(ticker, 'processed')
            return True

        except Exception as e:
            ticker = filing_info.get('ticker', 'unknown') if 'filing_info' in locals() else 'unknown'
            logger.error(f"Error processing filing {file_path} for {ticker}: {e}")
            self._update_stats(ticker, 'errors')
            return False    
            
    def process_all_new_filings(self):
        """Process all new filings in the filings directory."""
        logger.info("Starting processing of new filings...")
        processed_count = 0
        error_count = 0
        stats_by_company = {}

        for root, dirs, files in os.walk(FILINGS_DIR):
            for file in files:
                if file == FILING_FULL_SUBMISSION_FILENAME:
                    file_path = os.path.join(root, file)
                    try:
                        # Get company from path
                        path_parts = os.path.normpath(file_path).split(os.sep)
                        company = path_parts[path_parts.index(os.path.basename(FILINGS_DIR)) + 1]
                        
                        # Initialize company stats if needed
                        if company not in stats_by_company:
                            stats_by_company[company] = {'processed': 0, 'errors': 0}
                        
                        if self.process_filing(file_path):
                            processed_count += 1
                            stats_by_company[company]['processed'] += 1
                        else:
                            error_count += 1
                            stats_by_company[company]['errors'] += 1
                    except Exception as e:
                        logger.error(f"Error processing {file_path}: {e}", exc_info=True)
                        error_count += 1
                        if company in stats_by_company:
                            stats_by_company[company]['errors'] += 1        # Log detailed stats
        logger.info(f"Filing processing complete. Total Processed: {processed_count}, Total Errors: {error_count}")
        for company, stats in stats_by_company.items():
            logger.info(f"Company {company}: Processed {stats['processed']}, Errors {stats['errors']}")
        return processed_count
