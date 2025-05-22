import os
import sys
from pathlib import Path
import logging

# Add the app directory to the path so we can import our modules
app_path = str(Path(__file__).parent.parent)
if app_path not in sys.path:
    sys.path.append(app_path)

from app.services.sql_storage import SQLStorage
from app.core.config import BASE_DIR # Import BASE_DIR

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_database():
    logger.info("Starting database check")
    
    # Check if database file exists
    # Construct db_path consistent with sql_storage.py
    db_path = os.path.join(BASE_DIR, "data", "db", "sec_filings.db")
    logger.info(f"Database path: {db_path}")
    logger.info(f"Database exists: {os.path.exists(db_path)}")
    
    # Initialize SQLStorage with the potentially new DB_URL based on corrected BASE_DIR
    db_url = f"sqlite:///{db_path}"
    storage = SQLStorage(db_url=db_url)
    logger.info("Created SQLStorage instance")
    
    with storage.session_scope() as session:
        # Check tables exist
        print("\nChecking if tables exist:")
        print("-" * 50)
        try:
            filings_count = session.query(storage.Filing).count()
            print(f"Filings table exists - {filings_count} records")
        except Exception as e:
            print(f"Error checking Filings table: {e}")

        try:
            metrics_count = session.query(storage.Metric).count()
            print(f"Metrics table exists - {metrics_count} records")
        except Exception as e:
            print(f"Error checking Metrics table: {e}")

        # If there are filings, show some sample data
        if filings_count > 0:
            print("\nSample Filings:")
            print("-" * 50)
            filings = session.query(storage.Filing).limit(3).all()
            for filing in filings:
                print(f"ID: {filing.id}")
                print(f"Ticker: {filing.ticker}")
                print(f"Filing Type: {filing.filing_type}")
                print(f"Filing Date: {filing.filing_date}")
                print("-" * 30)

if __name__ == "__main__":
    check_database()
