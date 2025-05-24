# app/services/streamlit/vector_search.py
import os
from app.services.embedding import EmbeddingService
from app.services.sql_storage import SQLStorage
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class VectorSearchService:
    def __init__(self):
        """Initialize the vector search service for retrieving text from ChromaDB."""
        self.embedding_service = EmbeddingService()
        self.sql_storage = SQLStorage()
        self.collection = self.embedding_service.collection
        logger.info("VectorSearchService initialized successfully.")
    
    def reload(self):
        """Reload the service connections to pick up new data."""
        self.sql_storage = SQLStorage()
        self.embedding_service = EmbeddingService()
        self.collection = self.embedding_service.collection
        logger.info("VectorSearchService reloaded.")
    
    def get_filing_text_preview(self, ticker: str, filing_type: str, filing_id: str, max_chars: int = 1000) -> str:
        """Get a preview of the filing text.
        
        Args:
            ticker: The stock ticker symbol
            filing_type: The type of filing (e.g., '10-K', '10-Q')
            filing_id: The SEC accession number or filing date
            max_chars: Maximum number of characters to return
            
        Returns:
            str: A preview of the filing text
        """
        try:
            # First try to find by SEC accession number in file path or filing_id column
            cursor = self.sql_storage.conn.cursor()
            cursor.execute("""
                SELECT full_text FROM filings 
                WHERE ticker = ? AND filing_type = ? 
                AND (file_path LIKE ? OR filing_id = ?)
            """, (ticker, filing_type, f"%{filing_id}%", filing_id))
            
            result = cursor.fetchone()
            if not result:
                # If not found, try as a date
                cursor.execute("""
                    SELECT full_text FROM filings 
                    WHERE ticker = ? AND filing_type = ? 
                    AND filing_date = ?
                """, (ticker, filing_type, filing_id))
                result = cursor.fetchone()
            
            if not result:
                logger.warning(f"No filing found for {ticker} {filing_type} {filing_id}")
                return "Filing text not found."
                
            text = result[0]
            
            # Return a preview of the text
            preview = text[:max_chars] + "..." if len(text) > max_chars else text
            logger.info(f"Retrieved text preview for {ticker} {filing_type} {filing_id}")
            return preview
            
        except Exception as e:
            logger.error(f"Error retrieving filing text: {e}")
            return f"Error retrieving filing text: {str(e)}"
    
    def search_by_query(self, query: str, n_results: int = 3) -> list:
        """Search for relevant filing sections based on a query.
        
        Args:
            query: The search query
            n_results: Number of results to return
            
        Returns:
            list: Relevant filing sections with metadata
        """
        try:
            # Generate embedding for the query
            query_embedding = self.embedding_service.generate_embedding(query)
            if not query_embedding:
                logger.error("Failed to generate embedding for query.")
                return []
            
            # Query the collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["documents", "metadatas"]
            )
            
            # Format the results
            formatted_results = []
            if results and "documents" in results and results["documents"]:
                documents = results["documents"][0]  # First query's results
                metadatas = results["metadatas"][0] if "metadatas" in results else [{}] * len(documents)
                
                for doc, meta in zip(documents, metadatas):
                    formatted_results.append({
                        "text": doc,
                        "metadata": meta
                    })
            
            logger.info(f"Found {len(formatted_results)} relevant sections for query: {query}")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching by query: {e}")
            return []