import os
from pathlib import Path
import sys
from dotenv import load_dotenv
import argparse

# Load environment variables from .env file
load_dotenv()

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from app.services.processing_pipeline import ProcessingPipeline
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

def process_all_filings(force=False):
    """Process all SEC filings and store them in the database."""
    pipeline = ProcessingPipeline()
    filings_dir = Path(os.path.join(project_root, "docker", "sec-edgar-filings"))
    
    if not filings_dir.exists():
        logger.error(f"Filings directory not found: {filings_dir}")
        return
    
    # Process each filing for each ticker
    for ticker_dir in filings_dir.iterdir():
        if not ticker_dir.is_dir():
            continue
            
        ticker = ticker_dir.name
        logger.info(f"Processing filings for {ticker}")
        
        # Process each filing type (10-K, 10-Q, etc.)
        for filing_type_dir in ticker_dir.iterdir():
            if not filing_type_dir.is_dir():
                continue
                
            filing_type = filing_type_dir.name
            
            # Process each filing date
            for filing_date_dir in filing_type_dir.iterdir():
                if not filing_date_dir.is_dir():
                    continue
                    
                # Look for the full submission file
                full_submission = filing_date_dir / "full-submission.txt"
                if full_submission.exists():
                    logger.info(f"Processing {ticker} {filing_type} from {filing_date_dir.name} (force={force})")
                    try:
                        pipeline.process_and_store(ticker, filing_type, str(full_submission), force=force)
                    except Exception as e:
                        logger.error(f"Error processing {full_submission}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process all SEC filings and store them in the database.")
    parser.add_argument('--force', action='store_true', help='Force reprocessing of metrics for all filings')
    args = parser.parse_args()
    logger.info(f"Starting filing processing... (force={args.force})")
    process_all_filings(force=args.force)
    logger.info("Filing processing complete!")
