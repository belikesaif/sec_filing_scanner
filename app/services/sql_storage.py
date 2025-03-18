# app/services/sql_storage.py
import sqlite3
from sqlite3 import Connection
import os
from app.core.config import BASE_DIR
from app.utils.logger import setup_logger

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
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS filings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT,
                    filing_type TEXT,
                    filing_date TEXT,
                    file_path TEXT UNIQUE,
                    full_text TEXT
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filing_id INTEGER,
                    revenue TEXT,
                    net_income TEXT,
                    total_assets TEXT,
                    total_liabilities TEXT,
                    shareholders_equity TEXT,
                    FOREIGN KEY (filing_id) REFERENCES filings (id)
                );
            """)
            self.conn.commit()
            logger.info("SQLite tables created or verified.")
        except sqlite3.Error as e:
            logger.error(f"Error creating SQLite tables: {e}")

    def insert_filing(self, ticker: str, filing_type: str, filing_date: str, file_path: str, full_text: str) -> int:
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO filings (ticker, filing_type, filing_date, file_path, full_text)
                VALUES (?, ?, ?, ?, ?);
            """, (ticker, filing_type, filing_date, file_path, full_text))
            self.conn.commit()
            filing_id = cursor.lastrowid
            logger.info(f"Inserted filing record with ID {filing_id} for ticker {ticker}.")
            return filing_id
        except sqlite3.Error as e:
            logger.error(f"Error inserting filing record: {e}")
            return -1

    def insert_metrics(self, filing_id: int, metrics: dict):
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO metrics (filing_id, revenue, net_income, total_assets, total_liabilities, shareholders_equity)
                VALUES (?, ?, ?, ?, ?, ?);
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
