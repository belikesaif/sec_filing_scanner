"""Filing browser service for the Streamlit app."""
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import re
from app.services.sql_storage import SQLStorage
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class FilingBrowser:
    def __init__(self, filings_dir: str):
        self.filings_dir = Path(filings_dir)
        self.sql_storage = SQLStorage()
        logger.info(f"FilingBrowser initialized with directory: {filings_dir}")

    def extract_filing_date(self, filing_dir: Path) -> Optional[datetime]:
        """Extract filing date from full-submission.txt file."""
        try:
            full_submission = filing_dir / "full-submission.txt"
            if not full_submission.exists():
                return self.extract_date_from_path(filing_dir)
            
            # Read first 2000 bytes to look for date
            with open(full_submission, 'r', encoding='utf-8') as f:
                content = f.read(2000)
            
            # Look for various date patterns in order of preference
            
            # 1. PERIOD OF REPORT (most accurate for financial data)
            period_patterns = [
                r'PERIOD OF REPORT\s*:\s*(\d{4})-(\d{2})-(\d{2})',
                r'PERIOD OF REPORT\s*:\s*(\d{2})/(\d{2})/(\d{4})',
                r'CONFORMED PERIOD OF REPORT\s*:\s*(\d{8})'  # YYYYMMDD format
            ]
            
            for pattern in period_patterns:
                match = re.search(pattern, content)
                if match:
                    if len(match.groups()) == 3:
                        year, month, day = map(int, match.groups())
                        return datetime(year, month, day)
                    elif len(match.groups()) == 1:
                        # Handle YYYYMMDD format
                        date_str = match.group(1)
                        return datetime(int(date_str[:4]), int(date_str[4:6]), int(date_str[6:]))
            
            # 2. FILED date as backup
            filed_patterns = [
                r'FILED\s*:\s*(\d{4})-(\d{2})-(\d{2})',
                r'FILED\s*:\s*(\d{2})/(\d{2})/(\d{4})',
                r'FILED AS OF DATE\s*:\s*(\d{8})'  # YYYYMMDD format
            ]
            
            for pattern in filed_patterns:
                match = re.search(pattern, content)
                if match:
                    if len(match.groups()) == 3:
                        if pattern.endswith('(\d{4})'): # MM/DD/YYYY format
                            month, day, year = map(int, match.groups())
                        else: # YYYY-MM-DD format
                            year, month, day = map(int, match.groups())
                        return datetime(year, month, day)
                    elif len(match.groups()) == 1:
                        # Handle YYYYMMDD format
                        date_str = match.group(1)
                        return datetime(int(date_str[:4]), int(date_str[4:6]), int(date_str[6:]))
            
            # 3. Fallback to path date
            return self.extract_date_from_path(filing_dir)
            
        except Exception:
            return self.extract_date_from_path(filing_dir)
    
    def extract_date_from_path(self, filing_dir: Path) -> Optional[datetime]:
        """Extract date from filing directory name or path as last resort."""
        try:
            # Try to get the year from accession number (e.g., 0000320193-17-000070)
            parts = filing_dir.name.split('-')
            if len(parts) >= 2 and len(parts[1]) == 2:
                year = int(f"20{parts[1]}")  # e.g., "17" -> 2017
                return datetime(year, 1, 1)  # Default to Jan 1st
            return None
        except Exception:
            return None

    def get_filing_id_from_path(self, path: str) -> str:
        """Extract the SEC accession number from a filing path."""
        parts = os.path.normpath(path).split(os.sep)
        try:
            # Find the component that looks like an SEC accession number
            filing_id = next(p for p in parts if p.count('-') >= 2)
            return filing_id
        except Exception:
            return os.path.basename(path)

    def get_filings(self, ticker: str) -> List[Dict]:
        """Get all filings for a ticker with proper date sorting."""
        filings = []
        seen_filing_ids = set()
        
        logger.info(f"Getting filings for ticker: {ticker}")
        
        # First, get ALL filings from SQLite database (simplified query)
        try:
            cursor = self.sql_storage.conn.cursor()
            
            # Simple query to get all filings for the ticker
            cursor.execute("""
                SELECT 
                    f.id,
                    f.ticker, 
                    f.filing_type, 
                    f.filing_id, 
                    f.filing_date, 
                    f.file_path
                FROM filings f
                WHERE f.ticker = ?
                ORDER BY f.filing_date DESC, f.filing_type
            """, (ticker,))
            
            db_filings = cursor.fetchall()
            logger.info(f"Found {len(db_filings)} filings in database for {ticker}")
            
            # Remove deduplication by filing_id so all filings are included
            for row in db_filings:
                filing_db_id = row[0]  # database id
                filing_id = row[3]  # filing_id column
                
                try:
                    # Convert date string to datetime
                    filing_date = datetime.strptime(row[4], "%Y-%m-%d") if row[4] else datetime.now()
                    
                    # Check if this filing has valid metrics
                    cursor.execute("""
                        SELECT COUNT(*) FROM metrics 
                        WHERE filing_id = ? 
                        AND (revenue IS NOT NULL AND revenue != '' 
                             OR net_income IS NOT NULL AND net_income != ''
                             OR total_assets IS NOT NULL AND total_assets != ''
                             OR total_liabilities IS NOT NULL AND total_liabilities != ''
                             OR shareholders_equity IS NOT NULL AND shareholders_equity != '')
                    """, (filing_db_id,))
                    
                    has_metrics = cursor.fetchone()[0] > 0
                    
                    filings.append({
                        "ticker": row[1],
                        "filing_type": row[2],
                        "filing_id": filing_id,
                        "filing_date": filing_date,
                        "path": row[5],
                        "has_metrics": has_metrics
                    })
                    logger.debug(f"Added filing {filing_id} with metrics={has_metrics}")
                except Exception as e:
                    logger.error(f"Error processing database filing {filing_id}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Database error while fetching filings: {e}")

        # Then supplement with filesystem data for any new filings
        ticker_dir = self.filings_dir / ticker
        if ticker_dir.exists():
            try:
                fs_filing_count = 0
                for filing_type_dir in ticker_dir.iterdir():
                    if not filing_type_dir.is_dir():
                        continue
                        
                    filing_type = filing_type_dir.name
                    logger.debug(f"Checking filing type directory: {filing_type}")
                    
                    for filing_dir in filing_type_dir.iterdir():
                        if not filing_dir.is_dir():
                            continue
                            
                        if not (filing_dir / "full-submission.txt").exists():
                            continue
                            
                        filing_id = self.get_filing_id_from_path(str(filing_dir))
                        
                        if filing_id in seen_filing_ids:
                            continue
                            
                        try:
                            seen_filing_ids.add(filing_id)
                            filing_date = self.extract_filing_date(filing_dir)
                            
                            filings.append({
                                "ticker": ticker,
                                "filing_type": filing_type,
                                "filing_id": filing_id,
                                "filing_date": filing_date or datetime.now(),
                                "path": str(filing_dir),
                                "has_metrics": False  # Not yet in database
                            })
                            fs_filing_count += 1
                        except Exception as e:
                            logger.error(f"Error processing filesystem filing {filing_id}: {e}")
                            continue
                            
                logger.info(f"Found {fs_filing_count} additional filings on filesystem for {ticker}")
                
            except Exception as e:
                logger.error(f"Error reading from filesystem: {e}")
        else:
            logger.warning(f"Ticker directory not found: {ticker_dir}")
        
        # Sort filings by date (newest first) and type
        filings.sort(key=lambda x: (x["filing_date"], x["filing_type"]), reverse=True)
        
        logger.info(f"Total filings found for {ticker}: {len(filings)}")
        return filings
