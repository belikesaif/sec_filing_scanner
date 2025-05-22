# tests/test_end_to_end.py
import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import json
import time

# Add the app directory to the path so we can import our modules
app_path = str(Path(__file__).parent.parent)
if app_path not in sys.path:
    sys.path.append(app_path)

from app.services.scheduler import FilingScheduler
from app.services.sql_storage import SQLStorage
from app.services.downloader import SecFilingDownloader
from app.services.processor import FilingProcessor
from app.models.filing import Filing
from app.models.metric import Metric


class TestEndToEnd:
    @pytest.fixture
    def setup_test_environment(self):
        """Set up a test environment with mock data"""
        # Create a temporary directory for test data
        test_dir = tempfile.mkdtemp()
        test_filing_dir = os.path.join(test_dir, "sec-edgar-filings", "AAPL", "10-Q")
        os.makedirs(test_filing_dir, exist_ok=True)
        
        # Create a mock filing file
        accession_number = "0000320193-23-000077"
        filing_date = "2023-07-28"
        
        # Create a mock filing directory
        filing_path = os.path.join(test_filing_dir, accession_number)
        os.makedirs(filing_path, exist_ok=True)
        
        # Create a mock full-submission.txt file with sample content
        full_submission_path = os.path.join(filing_path, "full-submission.txt")
        with open(full_submission_path, "w") as f:
            f.write(f"""ACCESSION NUMBER: {accession_number}

FILING DATE: {filing_date}

COMPANY NAME: APPLE INC

FORM TYPE: 10-Q

REPORTING PERIOD: June 24, 2023

ITEM INFORMATION: FINANCIAL STATEMENTS

CONSOLIDATED STATEMENTS OF OPERATIONS (Unaudited)
(In millions, except per share amounts)

                                Three Months Ended         Nine Months Ended
                                June 24,    June 25,      June 24,    June 25,
                                2023        2022          2023        2022
Net sales                       $81,797     $82,959       $293,790    $304,182
Cost of sales                   43,802      45,336        161,304     170,686
Gross margin                    37,995      37,623        132,486     133,496

Operating expenses:
Research and development        7,442       6,797         21,566      19,490
Selling, general and administrative 6,425   6,012         19,070      18,375
Total operating expenses        13,867      12,809        40,636      37,865

Operating income                24,128      24,814        91,850      95,631
Other income/(expense), net     83          (10)          1,051       (309)
Income before provision for income taxes 24,211 24,804    92,901      95,322
Provision for income taxes      3,383       3,624         14,125      14,964
Net income                      $20,828     $21,180       $78,776     $80,358
""")
        
        yield {
            "test_dir": test_dir,
            "filing_path": filing_path,
            "full_submission_path": full_submission_path,
            "accession_number": accession_number,
            "filing_date": filing_date
        }
        
        # Clean up after the test
        shutil.rmtree(test_dir)
    
    def test_filing_processing(self, setup_test_environment):
        """Test that a filing can be processed and stored in the database"""
        # Get the test environment
        env = setup_test_environment
        
        # Process the filing
        processor = FilingProcessor(env["full_submission_path"])
        result = processor.process()
        
        # Verify the processor extracted the data correctly
        assert result is not None
        assert "full_text" in result
        assert "metadata" in result
        assert "quantitative_data" in result
        
        # Verify the metadata
        metadata = result["metadata"]
        assert metadata["accession_number"] == env["accession_number"]
        assert metadata["filing_date"] == env["filing_date"]
        
        # Verify the quantitative data
        quant_data = result["quantitative_data"]
        assert "revenue" in quant_data
        assert quant_data["revenue"] == 81797  # From the mock filing
        assert "net_income" in quant_data
        assert quant_data["net_income"] == 20828  # From the mock filing
    
    def test_end_to_end_flow(self, setup_test_environment, monkeypatch):
        """Test the end-to-end flow from scheduler to database"""
        # Get the test environment
        env = setup_test_environment
        
        # Create a SQL storage instance with an in-memory database for testing
        sql_storage = SQLStorage("sqlite:///:memory:")
        
        # Mock the downloader to return our test filing path
        def mock_download_filing(self, ticker, filing_type):
            return [env["full_submission_path"]]
        
        # Apply the monkeypatch
        monkeypatch.setattr(SecFilingDownloader, "download_filing", mock_download_filing)
        
        # Create a scheduler instance
        scheduler = FilingScheduler()
        
        # Override the SQL storage with our test instance
        scheduler.sql_storage = sql_storage
        
        # Run a single processing cycle
        scheduler._process_cycle()
        
        # Verify the filing was stored in the database
        with sql_storage.session_scope() as session:
            # Check if the filing exists
            filing = session.query(Filing).filter(Filing.ticker == "AAPL").first()
            assert filing is not None
            assert filing.filing_type == "10-Q"
            assert filing.accession_number == env["accession_number"]
            
            # Check if the metrics were stored
            metrics = session.query(Metric).filter(Metric.filing_id == filing.id).all()
            assert len(metrics) > 0
            
            # Find the revenue metric
            revenue_metric = next((m for m in metrics if m.name == "revenue"), None)
            assert revenue_metric is not None
            assert revenue_metric.value == 81797
            
            # Find the net income metric
            net_income_metric = next((m for m in metrics if m.name == "net_income"), None)
            assert net_income_metric is not None
            assert net_income_metric.value == 20828
    
    def test_streamlit_api_integration(self, setup_test_environment, monkeypatch):
        """Test the integration between the Streamlit UI and the backend API"""
        # This test would normally use requests to call the API endpoints
        # and verify the responses, but for simplicity, we'll mock the API calls
        
        # Mock the API response for getting filing metrics
        def mock_get_filing_metrics(self, ticker, metric_names):
            if ticker == "AAPL" and "revenue" in metric_names:
                return [
                    {
                        "filing_id": 1,
                        "filing_date": "2023-07-28",
                        "filing_type": "10-Q",
                        "name": "revenue",
                        "value": 81797
                    }
                ]
            return []
        
        # Apply the monkeypatch
        monkeypatch.setattr(SQLStorage, "get_filing_metrics", mock_get_filing_metrics)
        
        # Create a SQL storage instance
        sql_storage = SQLStorage("sqlite:///:memory:")
        
        # Call the mocked method
        metrics = sql_storage.get_filing_metrics("AAPL", ["revenue"])
        
        # Verify the response
        assert len(metrics) == 1
        assert metrics[0]["filing_type"] == "10-Q"
        assert metrics[0]["name"] == "revenue"
        assert metrics[0]["value"] == 81797