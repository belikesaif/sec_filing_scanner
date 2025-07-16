import sqlite3
import os
from pathlib import Path

# Build the path for the SQLite database file
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "data" / "db" / "sec_filings.db"

def fix_database():
    try:
        # Back up existing database
        if DB_PATH.exists():
            backup_path = DB_PATH.with_suffix('.db.bak')
            import shutil
            shutil.copy2(DB_PATH, backup_path)
            print(f"Created backup at {backup_path}")
        
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check for processing_status column
        cursor.execute("PRAGMA table_info(filings)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'processing_status' not in columns:
            print("Adding processing_status column to filings table...")
            cursor.execute("""
                ALTER TABLE filings ADD COLUMN processing_status TEXT DEFAULT 'completed'
            """)
            conn.commit()
        
        # Update any NULL values
        cursor.execute("UPDATE filings SET processing_status = 'completed' WHERE processing_status IS NULL")
        conn.commit()
        
        # Get filing counts
        cursor.execute("SELECT COUNT(*) FROM filings")
        total_filings = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM metrics")
        total_metrics = cursor.fetchone()[0]
        
        cursor.execute("SELECT ticker, COUNT(*) as count FROM filings GROUP BY ticker")
        ticker_counts = cursor.fetchall()
        
        print("\nDatabase Statistics:")
        print(f"Total Filings: {total_filings}")
        print(f"Total Metrics: {total_metrics}")
        print("\nFilings by Ticker:")
        for ticker, count in ticker_counts:
            print(f"{ticker}: {count}")
            
        conn.close()
        print("\nDatabase update completed successfully")
        
    except Exception as e:
        print(f"Error updating database: {e}")

if __name__ == "__main__":
    fix_database()
