import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.sql_storage import SQLStorage
from app.services.embedding import EmbeddingService
from app.services.processing_pipeline import ProcessingPipeline
# Import the config but override the FILINGS_DIR to use the correct path
from app.core.config import FILINGS_DIR as APP_FILINGS_DIR

# Use the correct filings directory at the project root
FILINGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sec-edgar-filings")

def ensure_directories():
    """Ensure all required directories exist"""
    # Check both root and app directories
    root_directories = [
        'data/db',
        'embeddings/chromadb'
    ]
    
    app_directories = [
        'app/data/db',
        'app/embeddings/chromadb'
    ]
    
    # Create directories in both locations to ensure compatibility
    for directory in root_directories + app_directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Ensured directory exists: {directory}")

def verify_database():
    """Verify database connection and tables"""
    sql_storage = SQLStorage()
    if not sql_storage.conn:
        logger.error("Failed to connect to database")
        return False
    
    logger.info("Database connection successful")
    
    # Check tables
    cursor = sql_storage.conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='filings'")
    if not cursor.fetchone():
        logger.error("Filings table does not exist")
        return False
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='metrics'")
    if not cursor.fetchone():
        logger.error("Metrics table does not exist")
        return False
    
    # Get the count of filings
    cursor.execute("SELECT COUNT(*) FROM filings")
    filings_count = cursor.fetchone()[0]
    logger.info(f"Database contains {filings_count} filings")
    
    # Get the count of metrics
    cursor.execute("SELECT COUNT(*) FROM metrics")
    metrics_count = cursor.fetchone()[0]
    logger.info(f"Database contains {metrics_count} metrics records")
    
    logger.info("Database tables verified")
    return True

def verify_embeddings():
    """Verify embedding service"""
    try:
        embedding_service = EmbeddingService()
        count = embedding_service.collection.count()
        logger.info(f"ChromaDB collection contains {count} embeddings")
        return True
    except Exception as e:
        logger.error(f"Error verifying embeddings: {e}")
        return False

def process_all_filings():
    """Process all filings in the filings directory"""
    pipeline = ProcessingPipeline()
    
    # Force processing of all filings, even if they've been processed before
    filings_processed = 0
    
    for ticker_dir in Path(FILINGS_DIR).iterdir():
        if not ticker_dir.is_dir():
            continue
        
        ticker = ticker_dir.name
        logger.info(f"Processing filings for ticker: {ticker}")
        
        for filing_type_dir in ticker_dir.iterdir():
            if not filing_type_dir.is_dir():
                continue
            
            filing_type = filing_type_dir.name
            
            for filing_dir in filing_type_dir.iterdir():
                if not filing_dir.is_dir():
                    continue
                
                filing_date = filing_dir.name
                full_submission_file = filing_dir / "full-submission.txt"
                
                if full_submission_file.exists():
                    logger.info(f"Processing filing: {ticker} - {filing_type} - {filing_date}")
                    
                    # Process the filing regardless of whether it exists in the database
                    pipeline.process_and_store(ticker, filing_type, str(full_submission_file))
                    filings_processed += 1
    
    logger.info(f"Processed {filings_processed} filings")
    return filings_processed

def main():
    """Main function to debug and fix database and embedding issues"""
    logger.info("Starting debug and fix process")
    
    # Step 1: Ensure directories exist
    ensure_directories()
    
    # Step 2: Verify database
    db_ok = verify_database()
    if not db_ok:
        logger.error("Database verification failed")
    
    # Step 3: Verify embeddings
    embeddings_ok = verify_embeddings()
    if not embeddings_ok:
        logger.error("Embeddings verification failed")
    
    # Step 4: Process all filings
    filings_processed = process_all_filings()
    
    # Step 5: Final verification
    db_ok_after = verify_database()
    embeddings_ok_after = verify_embeddings()
    
    logger.info("Debug and fix process completed")
    logger.info(f"Database status: {'OK' if db_ok_after else 'Failed'}")
    logger.info(f"Embeddings status: {'OK' if embeddings_ok_after else 'Failed'}")
    logger.info(f"Filings processed: {filings_processed}")
    
    # Step 6: Print summary and guidance
    print("\n" + "=" * 80)
    print("SEC FILING SCANNER - DEBUG AND FIX SUMMARY")
    print("=" * 80)
    print(f"Database status: {'✅ OK' if db_ok_after else '❌ Failed'}")
    print(f"Embeddings status: {'✅ OK' if embeddings_ok_after else '❌ Failed'}")
    print(f"Filings processed: {filings_processed}")
    print("\nIMPORTANT LOCATIONS:")
    print(f"- Database file: {os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'data', 'db', 'sec_filings.db')}")
    print(f"- Embeddings directory: {os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'embeddings', 'chromadb')}")
    print(f"- SEC filings directory: {FILINGS_DIR}")
    print("\nNEXT STEPS:")
    print("1. Run the Streamlit app: python streamlit_app.py")
    print("2. Browse filings, view metrics, and use the chat interface")
    print("=" * 80)

if __name__ == "__main__":
    main()