import os
import sys
from pathlib import Path
import logging
from datetime import datetime

# Add the app directory to the path so we can import our modules
app_path = str(Path(__file__).parent.parent)
if app_path not in sys.path:
    sys.path.append(app_path)

from app.services.sql_storage import SQLStorage

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_test_data():
    logger.info("Initializing test data")
    
    storage = SQLStorage()
    
    # Sample data
    test_filings = [
        {
            "ticker": "AAPL",
            "filing_type": "10-K",
            "filing_date": "2024-10-27",
            "file_path": "/path/to/filing1.html",
            "full_text": "Sample text for Apple's 10-K filing",
            "accession_number": "0000320193-24-000123"
        },
        {
            "ticker": "MSFT",
            "filing_type": "10-Q",
            "filing_date": "2024-04-15",
            "file_path": "/path/to/filing2.html",
            "full_text": "Sample text for Microsoft's 10-Q filing",
            "accession_number": "0000789019-24-000456"
        }
    ]
    
    try:
        for filing_data in test_filings:
            # Insert filing
            filing_id = storage.insert_filing(
                ticker=filing_data["ticker"],
                filing_type=filing_data["filing_type"],
                filing_date=filing_data["filing_date"],
                file_path=filing_data["file_path"],
                full_text=filing_data["full_text"],
                accession_number=filing_data["accession_number"]
            )
            
            if filing_id != -1:
                logger.info(f"Inserted filing {filing_id}")
                
                # Add some test metrics
                metrics = {
                    "revenue": 1000000000.0,
                    "net_income": 500000000.0,
                    "total_assets": 2000000000.0
                }
                
                if storage.insert_metrics(filing_id, metrics):
                    logger.info(f"Inserted metrics for filing {filing_id}")
            else:
                logger.error(f"Failed to insert filing for {filing_data['ticker']}")
                
    except Exception as e:
        logger.error(f"Error initializing test data: {e}")

if __name__ == "__main__":
    init_test_data()
