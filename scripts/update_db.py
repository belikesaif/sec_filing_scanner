import os
import sys
import sqlite3
from pathlib import Path

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from app.utils.logger import setup_logger
from app.core.config import BASE_DIR

logger = setup_logger(__name__)

def update_database():
    """Update the database schema and reprocess metrics if needed."""
    db_path = os.path.join(BASE_DIR, "data", "db", "sec_filings.db")
    
    try:
        # Ensure database directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create tables if they don't exist
        logger.info("Creating or updating tables...")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS filings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                filing_type TEXT NOT NULL,
                filing_date TEXT NOT NULL,
                file_path TEXT UNIQUE,
                full_text TEXT,
                UNIQUE(ticker, filing_type, filing_date)
            );
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filing_id INTEGER,
                revenue NUMERIC,
                net_income NUMERIC,
                total_assets NUMERIC,
                total_liabilities NUMERIC,
                shareholders_equity NUMERIC,
                FOREIGN KEY (filing_id) REFERENCES filings (id)
            );
        """)
        
        # Add indexes for better performance
        logger.info("Adding database indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_filings_ticker ON filings(ticker);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_filings_type ON filings(filing_type);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_filings_date ON filings(filing_date);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_filings_path ON filings(file_path);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_filing_id ON metrics(filing_id);")
        
        # Check for any filings without metrics
        cursor.execute("""
            SELECT f.id, f.ticker, f.filing_type, f.file_path
            FROM filings f
            LEFT JOIN metrics m ON f.id = m.filing_id
            WHERE m.id IS NULL
        """)
        missing_metrics = cursor.fetchall()
        
        if missing_metrics:
            logger.warning(f"Found {len(missing_metrics)} filings without metrics. Running metrics extraction...")
            from app.services.processor import FilingProcessor
            from app.services.sql_storage import SQLStorage
            
            sql_storage = SQLStorage()
            for filing_id, ticker, filing_type, file_path in missing_metrics:
                try:
                    processor = FilingProcessor(file_path)
                    result = processor.process()
                    if result and 'quantitative_data' in result:
                        sql_storage.insert_metrics(filing_id, result['quantitative_data'])
                        logger.info(f"Added metrics for {ticker} {filing_type} (ID: {filing_id})")
                except Exception as e:
                    logger.error(f"Error processing metrics for {file_path}: {e}")
        
        conn.commit()
        logger.info("Database update completed successfully.")
        
    except Exception as e:
        logger.error(f"Error updating database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    logger.info("Starting database update...")
    update_database()
    logger.info("Database update completed.")
