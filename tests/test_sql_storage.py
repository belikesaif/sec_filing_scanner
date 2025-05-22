import pytest
from datetime import datetime
from app.services.sql_storage import SQLStorage
from app.models.filing import Filing
from app.models.metric import Metric
import os
import tempfile

@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    db_fd, db_path = tempfile.mkstemp()
    db_url = f"sqlite:///{db_path}"
    
    # Create storage instance with test database
    storage = SQLStorage(db_url=db_url)
    
    # Run migrations to set up schema
    storage.run_migrations()
    
    yield storage
    
    # Clean up
    os.close(db_fd)
    os.unlink(db_path)

def test_insert_filing(temp_db):
    """Test inserting a filing record."""
    filing_id = temp_db.insert_filing(
        ticker="AAPL",
        filing_type="10-K",
        filing_date="2025-01-01",
        file_path="/path/to/filing.html",
        full_text="Sample filing text",
        accession_number="0000123456-25-000001"
    )
    
    assert filing_id != -1
    
    # Verify the filing exists
    with temp_db.session_scope() as session:
        filing = session.query(Filing).filter_by(id=filing_id).first()
        assert filing is not None
        assert filing.ticker == "AAPL"
        assert filing.filing_type == "10-K"

def test_insert_metrics(temp_db):
    """Test inserting metrics for a filing."""
    # First insert a filing
    filing_id = temp_db.insert_filing(
        ticker="AAPL",
        filing_type="10-K",
        filing_date="2025-01-01",
        file_path="/path/to/filing.html",
        full_text="Sample filing text",
        accession_number="0000123456-25-000001"
    )
    
    # Then insert metrics
    metrics_data = {
        'revenue': 1000000000.0,
        'net_income': 500000000.0
    }
    
    success = temp_db.insert_metrics(filing_id, metrics_data)
    assert success
    
    # Verify the metrics exist
    with temp_db.session_scope() as session:
        metrics = session.query(Metric).filter_by(filing_id=filing_id).all()
        assert len(metrics) == 2
        
        revenue_metric = next(m for m in metrics if m.metric_name == 'revenue')
        assert revenue_metric.value == 1000000000.0
        
        income_metric = next(m for m in metrics if m.metric_name == 'net_income')
        assert income_metric.value == 500000000.0

def test_get_filing_metrics(temp_db):
    """Test retrieving metrics for filings."""
    # Insert test data
    filing_id = temp_db.insert_filing(
        ticker="AAPL",
        filing_type="10-K",
        filing_date="2025-01-01",
        file_path="/path/to/filing.html",
        full_text="Sample filing text",
        accession_number="0000123456-25-000001"
    )
    
    metrics_data = {
        'revenue': 1000000000.0,
        'net_income': 500000000.0
    }
    temp_db.insert_metrics(filing_id, metrics_data)
    
    # Test retrieving metrics
    results = temp_db.get_filing_metrics(
        ticker="AAPL",
        metric_names=['revenue'],
        start_date="2024-01-01",
        end_date="2025-12-31"
    )
    
    assert len(results) == 1
    assert results[0]['metric_name'] == 'revenue'
    assert results[0]['value'] == 1000000000.0

def test_filing_exists(temp_db):
    """Test checking if a filing exists."""
    file_path = "/path/to/unique/filing.html"
    
    # Initially should not exist
    assert not temp_db.filing_exists(file_path)
    
    # Insert a filing
    temp_db.insert_filing(
        ticker="AAPL",
        filing_type="10-K",
        filing_date="2025-01-01",
        file_path=file_path,
        full_text="Sample filing text",
        accession_number="0000123456-25-000001"
    )
    
    # Now should exist
    assert temp_db.filing_exists(file_path)

def test_get_filing_by_accession(temp_db):
    """Test retrieving a filing by accession number."""
    accession = "0000123456-25-000001"
    
    # Insert a filing
    temp_db.insert_filing(
        ticker="AAPL",
        filing_type="10-K",
        filing_date="2025-01-01",
        file_path="/path/to/filing.html",
        full_text="Sample filing text",
        accession_number=accession
    )
    
    # Retrieve the filing
    filing = temp_db.get_filing_by_accession(accession)
    assert filing is not None
    assert filing.accession_number == accession
    assert filing.ticker == "AAPL"
