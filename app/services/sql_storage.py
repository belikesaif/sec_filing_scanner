# app/services/sql_storage.py
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from app.models.filing import Filing, Base
from app.models.metric import Metric
from app.core.config import BASE_DIR
import os
from app.utils.logger import setup_logger
from typing import Dict, List, Optional, Union
from contextlib import contextmanager

logger = setup_logger(__name__)

# Build the path for the SQLite database file
DB_PATH = os.path.join(BASE_DIR, "data", "db", "sec_filings.db")
DB_URL = f"sqlite:///{DB_PATH}"

class SQLStorage:
    def __init__(self, db_url: str = DB_URL):
        self.db_url = db_url
        self.engine = self._create_engine()
        # Store model classes as attributes for easy access
        self.Base = Base
        self.Filing = Filing
        self.Metric = Metric
        # Create all tables if they don't exist
        self.Base.metadata.create_all(self.engine)
        self.Session = scoped_session(sessionmaker(bind=self.engine))
    
    def _create_engine(self):
        # Ensure database directory exists
        db_dir = os.path.dirname(DB_PATH)
        os.makedirs(db_dir, exist_ok=True)
        
        return create_engine(self.db_url)
    
    @contextmanager
    def session_scope(self):
        """Provide a transactional scope around a series of operations."""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
    
    def filing_exists(self, file_path: str) -> bool:
        """Check if a filing with the given file path exists."""
        with self.session_scope() as session:
            return session.query(Filing).filter(Filing.file_path == file_path).first() is not None
    
    def get_filing_by_accession(self, accession: str) -> Optional[Filing]:
        """Get a filing by its accession number."""
        with self.session_scope() as session:
            return session.query(Filing).filter(Filing.accession_number == accession).first()
    
    def insert_filing(self, ticker: str, filing_type: str, filing_date: Union[str, datetime], file_path: str, 
                     full_text: str, accession_number: str) -> int:
        """Insert a new filing record."""
        try:
            with self.session_scope() as session:
                if isinstance(filing_date, str):
                    filing_date = datetime.strptime(filing_date, "%Y-%m-%d")
                
                filing = Filing(
                    ticker=ticker,
                    filing_type=filing_type,
                    filing_date=filing_date,
                    file_path=file_path,
                    full_text=full_text,
                    accession_number=accession_number,
                    processed_at=datetime.utcnow()
                )
                session.add(filing)
                session.flush()  # This will populate the id
                return filing.id
        except Exception as e:
            logger.error(f"Error inserting filing record: {e}")
            return -1
    
    def insert_metrics(self, filing_id: int, metrics_data: Dict[str, float]) -> bool:
        """Insert metrics for a filing."""
        try:
            with self.session_scope() as session:
                for metric_name, value in metrics_data.items():
                    if value is not None:
                        metric = Metric(
                            filing_id=filing_id,
                            metric_name=metric_name,
                            value=float(value),
                            unit='USD',
                            scale='normalized',
                            raw_value=str(value),
                            extracted_from='processor'
                        )
                        session.add(metric)
                return True
        except Exception as e:
            logger.error(f"Error inserting metrics: {e}")
            return False
    
    def get_filing_metrics(self, ticker: str, metric_names: Optional[List[str]] = None, 
                         start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict]:
        """Get metrics for filings matching the criteria."""
        try:
            with self.session_scope() as session:
                query = session.query(Filing, Metric).join(Metric)
                
                # Apply filters
                query = query.filter(Filing.ticker == ticker)
                
                if metric_names:
                    query = query.filter(Metric.metric_name.in_(metric_names))
                
                if start_date:
                    query = query.filter(Filing.filing_date >= start_date)
                
                if end_date:
                    query = query.filter(Filing.filing_date <= end_date)
                
                # Order by date
                query = query.order_by(Filing.filing_date.desc())
                
                results = []
                for filing, metric in query.all():
                    results.append({
                        'filing_id': filing.id,
                        'filing_type': filing.filing_type,
                        'filing_date': filing.filing_date.strftime("%Y-%m-%d"),
                        'metric_name': metric.metric_name,
                        'value': metric.value,
                        'unit': metric.unit,
                        'scale': metric.scale
                    })
                
                return results
        except Exception as e:
            logger.error(f"Error getting filing metrics: {e}")
            return []
    
    def run_migrations(self):
        """Run any pending database migrations."""
        try:
            from alembic.config import Config
            from alembic import command
            import os
            
            # Get the directory containing this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Navigate up to the project root where alembic.ini is located
            project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
            
            # Create Alembic configuration object
            alembic_cfg = Config(os.path.join(project_root, 'alembic.ini'))
            
            # Run the migration
            command.upgrade(alembic_cfg, "head")
            logger.info("Database migrations completed successfully")
        except Exception as e:
            logger.error(f"Error running database migrations: {e}")
            raise
