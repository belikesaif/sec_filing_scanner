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
    
    def process_and_store(self, ticker: str, filing_type: str, file_path: str):
        """
        Processes a single filing: extracts text and quantitative data, stores the filing in SQLite,
        and generates/stores its embedding in ChromaDB.
        """
        processor = FilingProcessor(file_path)
        result = processor.process()
        if not result:
            logger.error(f"Processing failed for file {file_path}.")
            return
        
        full_text = result.get("full_text", "")
        quantitative_data = result.get("quantitative_data", {})
        
        # Use current date as a placeholder for the filing date.
        filing_date = datetime.now().strftime("%Y-%m-%d")
        
        # Insert filing record into SQLite
        filing_id = self.sql_storage.insert_filing(ticker, filing_type, filing_date, file_path, full_text)
        if filing_id == -1:
            logger.error(f"Failed to insert filing record for file {file_path}.")
            return
        
        # Insert extracted quantitative metrics into SQLite
        self.sql_storage.insert_metrics(filing_id, quantitative_data)
        
        # Generate and store text embeddings for the filing
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
