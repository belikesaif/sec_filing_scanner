import os
from datetime import datetime
from app.utils.logger import setup_logger
from app.services.sql_storage import SQLStorage
from app.services.processor import FilingProcessor
from app.services.embedding import EmbeddingService
from app.core.config import FILINGS_DIR, FILING_FULL_SUBMISSION_FILENAME

logger = setup_logger(__name__)

class ProcessingPipeline:
    def __init__(self):
        self.sql_storage = SQLStorage()
        self.embedding_service = EmbeddingService()
    
    def process_and_store(self, ticker: str, filing_type: str, file_path: str, force: bool = False):
        """
        Processes a single filing: extracts text and quantitative data, stores the filing in SQLite,
        and generates/stores its embedding in ChromaDB.
        If force=True, always re-extract and re-insert metrics for the filing.
        """
        filing_exists = self.sql_storage.filing_exists(file_path)
        if filing_exists and not force:
            logger.info(f"Filing already exists in database, skipping: {file_path}")
            return

        # Extract filing ID and date from the path
        parts = os.path.normpath(file_path).split(os.sep)
        try:
            # The filing ID directory contains the filing date information
            filing_id_dir = next(p for p in parts if p.count('-') >= 2)  # Format: 0000320193-17-000070
            filing_year = filing_id_dir.split('-')[1]
            filing_date = f"20{filing_year}-01-01"  # Default to Jan 1st since exact date needs parsing from content
        except Exception as e:
            logger.warning(f"Could not extract filing date from path {file_path}, using current date: {e}")
            filing_date = datetime.now().strftime("%Y-%m-%d")

        processor = FilingProcessor(file_path)
        result = processor.process()
        if not result:
            logger.error(f"Processing failed for file {file_path}.")
            return

        full_text = result.get("full_text", "")
        quantitative_data = result.get("quantitative_data", {})
        content_filing_date = result.get("filing_date")

        # Use the filing date from content if available, otherwise use the one from path
        if content_filing_date:
            filing_date = content_filing_date

        # Insert or update filing record into SQLite
        filing_id = self.sql_storage.insert_filing(ticker, filing_type, filing_date, file_path, full_text)
        if filing_id == -1:
            logger.error(f"Failed to insert filing record for file {file_path}.")
            return

        # If force, delete old metrics for this filing_id before inserting new ones
        if force:
            try:
                cursor = self.sql_storage.conn.cursor()
                cursor.execute("DELETE FROM metrics WHERE filing_id = ?", (filing_id,))
                self.sql_storage.conn.commit()
                logger.info(f"Deleted old metrics for filing ID {filing_id} (force mode)")
            except Exception as e:
                logger.error(f"Error deleting old metrics for filing ID {filing_id}: {e}")

        # Insert extracted quantitative metrics into SQLite
        self.sql_storage.insert_metrics(filing_id, quantitative_data)

        # Generate and store text embeddings for the filing (optional: skip if not force and already exists)
        if not filing_exists or force:
            self.embedding_service.store_embedding(str(filing_id), full_text, metadata={
                "ticker": ticker,
                "filing_type": filing_type,
                "filing_date": filing_date
            })

        logger.info(f"Processing pipeline completed for file {file_path}.")

    def process_all_new_filings(self):
        """
        Traverses the filings directory (sec-edgar-filings) to find new filings (files named as FILING_FULL_SUBMISSION_FILENAME).
        For each new filing that hasn't been processed (determined via file_path uniqueness), it triggers processing.
        Expected folder structure: FILINGS_DIR/<ticker>/<filing_type>/<unique_filing_id>/full-submission.txt
        """
        for root, dirs, files in os.walk(FILINGS_DIR):
            for file in files:
                if file == FILING_FULL_SUBMISSION_FILENAME:
                    file_path = os.path.join(root, file)
                    # Extract ticker and filing_type from the folder path
                    parts = os.path.normpath(file_path).split(os.sep)
                    try:
                        filings_index = parts.index(os.path.basename(FILINGS_DIR))
                        ticker = parts[filings_index + 1]
                        filing_type = parts[filings_index + 2]
                    except Exception as e:
                        logger.error(f"Error parsing path {file_path}: {e}")
                        continue
                    
                    # Skip if this filing is already processed
                    if self.sql_storage.filing_exists(file_path):
                        continue
                    
                    # Process the new filing
                    logger.info(f"Processing new filing: {file_path}")
                    self.process_and_store(ticker, filing_type, file_path)
