# app/services/sql_storage.py
import sqlite3
from sqlite3 import Connection
import os
from app.core.config import BASE_DIR
from app.utils.logger import setup_logger
import pandas as pd
from typing import List, Dict, Any, Optional

logger = setup_logger(__name__)

# Build the path for the SQLite database file.
DB_PATH = os.path.join(BASE_DIR, "data", "db", "sec_filings.db")

class SQLStorage:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.conn = self.create_connection()
        if self.conn:
            self.create_tables()

    def create_connection(self) -> Connection:
        try:
            # Ensure that the directory for the database file exists.
            db_dir = os.path.dirname(self.db_path)
            os.makedirs(db_dir, exist_ok=True)
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            logger.info(f"Connected to SQLite database at {self.db_path}")
            return conn
        except sqlite3.Error as e:
            logger.error(f"SQLite connection error: {e}")
            return None
            
    def create_tables(self):
        try:
            cursor = self.conn.cursor()
            
            # Update filings table schema to include filing_id in uniqueness constraint
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS filings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    filing_type TEXT NOT NULL,
                    filing_date TEXT NOT NULL,
                    filing_id TEXT NOT NULL,
                    file_path TEXT UNIQUE,
                    full_text TEXT,
                    processing_status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(ticker, filing_type, filing_date, filing_id)
                );
            """)
            
            # Create metrics table with numeric columns
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filing_id INTEGER,
                    revenue NUMERIC,
                    net_income NUMERIC,
                    total_assets NUMERIC,
                    total_liabilities NUMERIC,
                    shareholders_equity NUMERIC,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (filing_id) REFERENCES filings (id)
                );
            """)
            
            # Create indexes for better search performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_filings_ticker ON filings(ticker);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_filings_type ON filings(filing_type);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_filings_date ON filings(filing_date);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_filings_path ON filings(file_path);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_filings_filing_id ON filings(filing_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_filing_id ON metrics(filing_id);")
            
            self.conn.commit()
            logger.info("SQLite tables and indexes created or verified.")
        except sqlite3.Error as e:
            logger.error(f"Error creating SQLite tables: {e}")

    def insert_filing(self, ticker: str, filing_type: str, filing_date: str, file_path: str, full_text: str) -> int:
        try:
            # Extract filing_id from file_path
            filing_id_val = None
            parts = os.path.normpath(file_path).split(os.sep)
            try:
                # Find the component that looks like an SEC accession number (e.g., 0000320193-17-000070)
                filing_id_val = next(p for p in parts if p.count('-') >= 2)
            except Exception:
                # If we can't extract a filing_id, use the basename as fallback
                filing_id_val = os.path.basename(os.path.dirname(file_path))

            cursor = self.conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO filings (ticker, filing_type, filing_date, filing_id, file_path, full_text)
                    VALUES (?, ?, ?, ?, ?, ?);
                """, (ticker, filing_type, filing_date, filing_id_val, file_path, full_text))
                self.conn.commit()
                filing_row_id = cursor.lastrowid
                logger.info(f"Inserted filing record with ID {filing_row_id} for ticker {ticker}.")
                return filing_row_id
            except sqlite3.IntegrityError as e:
                # If unique constraint failed, update the existing record and fetch its id
                logger.info(f"Filing already exists, updating instead: {e}")
                cursor.execute("""
                    SELECT id FROM filings WHERE ticker = ? AND filing_type = ? AND filing_date = ? AND filing_id = ?
                """, (ticker, filing_type, filing_date, filing_id_val))
                row = cursor.fetchone()
                if row:
                    filing_row_id = row[0]
                    cursor.execute("""
                        UPDATE filings SET full_text = ?, file_path = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
                    """, (full_text, file_path, filing_row_id))
                    self.conn.commit()
                    logger.info(f"Updated filing record with ID {filing_row_id} for ticker {ticker}.")
                    return filing_row_id
                else:
                    logger.error(f"Filing exists but could not fetch its ID for update.")
                    return -1
        except sqlite3.Error as e:
            logger.error(f"Error inserting or updating filing record: {e}")
            return -1

    def insert_metrics(self, filing_id: int, metrics: dict):
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO metrics (filing_id, revenue, net_income, total_assets, total_liabilities, shareholders_equity, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
            """, (
                filing_id,
                metrics.get("revenue"),
                metrics.get("net_income"),
                metrics.get("total_assets"),
                metrics.get("total_liabilities"),
                metrics.get("shareholders_equity")
            ))
            self.conn.commit()
            logger.info(f"Inserted metrics for filing ID {filing_id}.")
        except sqlite3.Error as e:
            logger.error(f"Error inserting metrics for filing ID {filing_id}: {e}")

    def filing_exists(self, file_path: str) -> bool:
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM filings WHERE file_path = ?", (file_path,))
            count = cursor.fetchone()[0]
            return count > 0
        except Exception as e:
            logger.error(f"Error checking if filing exists: {e}")
            return False

    def validate_database(self) -> Dict[str, Any]:
        """Validate database structure and integrity."""
        status = {
            "status": "healthy",
            "tables": {},
            "issues": []
        }
        
        expected_tables = {
            "filings": [
                "id", "ticker", "filing_type", "filing_date", 
                "file_path", "full_text"
            ],
            "metrics": [
                "id", "filing_id", "revenue", "net_income",
                "total_assets", "total_liabilities", "shareholders_equity"
            ]
        }
        
        try:
            cursor = self.conn.cursor()
            
            # Check each expected table
            for table, expected_columns in expected_tables.items():
                try:
                    cursor.execute(f"SELECT * FROM {table} LIMIT 1")
                    columns = [description[0] for description in cursor.description]
                    
                    status["tables"][table] = {
                        "exists": True,
                        "columns": columns,
                        "missing_columns": [col for col in expected_columns if col not in columns],
                        "extra_columns": [col for col in columns if col not in expected_columns]
                    }
                    
                except sqlite3.Error as e:
                    status["status"] = "degraded"
                    status["tables"][table] = {"exists": False, "error": str(e)}
                    status["issues"].append(f"Table '{table}' validation failed: {e}")
            
            # Check for orphaned records in metrics
            cursor.execute("""
                SELECT COUNT(*) FROM metrics m 
                LEFT JOIN filings f ON m.filing_id = f.id 
                WHERE f.id IS NULL
            """)
            orphaned_count = cursor.fetchone()[0]
            if orphaned_count > 0:
                status["issues"].append(f"Found {orphaned_count} orphaned metrics records")
                status["status"] = "degraded"
            
        except Exception as e:
            status["status"] = "error"
            status["issues"].append(f"Database validation failed: {e}")
            logger.error(f"Database validation failed: {e}")
        
        return status
    
    def repair_database(self) -> bool:
        """Attempt to repair database issues."""
        try:
            cursor = self.conn.cursor()
            
            # Remove orphaned metrics
            cursor.execute("""
                DELETE FROM metrics 
                WHERE filing_id NOT IN (SELECT id FROM filings)
            """)
            
            # Ensure indices exist
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_filings_ticker 
                ON filings (ticker)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_filings_type 
                ON filings (filing_type)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_metrics_filing_id 
                ON metrics (filing_id)
            """)
            
            self.conn.commit()
            logger.info("Database repair completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Database repair failed: {e}")
            return False

    def get_filing_text(self, ticker: str, filing_type: str, filing_id: str) -> Optional[str]:
        """Get the full text of a filing."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT full_text
                FROM filings
                WHERE ticker = ? AND filing_type = ? AND filing_id = ?
            """, (ticker, filing_type, filing_id))
            
            result = cursor.fetchone()
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"Error retrieving filing text: {e}")
            return None
