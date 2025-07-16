import os
import sys
import unittest
from pathlib import Path

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.sql_storage import SQLStorage
from app.services.embedding import EmbeddingService
from app.services.processing_pipeline import ProcessingPipeline
from app.core.config import FILINGS_DIR

class TestDataPipeline(unittest.TestCase):
    def setUp(self):
        # Create test directories if they don't exist
        os.makedirs('data/db', exist_ok=True)
        os.makedirs('embeddings/chromadb', exist_ok=True)
        
        # Initialize services
        self.sql_storage = SQLStorage()
        self.embedding_service = EmbeddingService()
        self.pipeline = ProcessingPipeline()
    
    def test_database_connection(self):
        """Test that the database connection is working"""
        self.assertIsNotNone(self.sql_storage.conn, "Database connection failed")
        
    def test_tables_exist(self):
        """Test that the required tables exist in the database"""
        cursor = self.sql_storage.conn.cursor()
        
        # Check filings table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='filings'")
        self.assertIsNotNone(cursor.fetchone(), "Filings table does not exist")
        
        # Check metrics table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='metrics'")
        self.assertIsNotNone(cursor.fetchone(), "Metrics table does not exist")
    
    def test_embedding_service(self):
        """Test that the embedding service is working"""
        # Generate a test embedding
        test_text = "This is a test document for embedding generation."
        embedding = self.embedding_service.generate_embedding(test_text)
        self.assertTrue(len(embedding) > 0, "Failed to generate embedding")
        
        # Test storing an embedding
        self.embedding_service.store_embedding(
            "test_id", 
            test_text, 
            metadata={"ticker": "TEST", "filing_type": "10-K", "filing_date": "2023-01-01"}
        )
        
        # Verify the embedding was stored
        count = self.embedding_service.collection.count()
        self.assertTrue(count > 0, "Failed to store embedding")
    
    def test_filing_exists(self):
        """Test the filing_exists method"""
        # Test with a non-existent file path
        self.assertFalse(self.sql_storage.filing_exists("non_existent_path"))
    
    def test_filings_directory(self):
        """Test that the filings directory exists and contains expected structure"""
        filings_dir = Path(FILINGS_DIR)
        self.assertTrue(filings_dir.exists(), f"Filings directory {FILINGS_DIR} does not exist")
        
        # Check if there are any ticker directories
        ticker_dirs = [d for d in filings_dir.iterdir() if d.is_dir()]
        self.assertTrue(len(ticker_dirs) > 0, "No ticker directories found in filings directory")
        
        # Check if there are filing type directories for the first ticker
        if ticker_dirs:
            filing_type_dirs = [d for d in ticker_dirs[0].iterdir() if d.is_dir()]
            self.assertTrue(len(filing_type_dirs) > 0, f"No filing type directories found for {ticker_dirs[0].name}")

if __name__ == '__main__':
    unittest.main()