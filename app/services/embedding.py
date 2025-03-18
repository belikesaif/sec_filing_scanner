import os
from sentence_transformers import SentenceTransformer
import chromadb
from app.utils.logger import setup_logger
from app.core.config import BASE_DIR

logger = setup_logger(__name__)

class EmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        
        # Define a persistent path for ChromaDB
        # Make sure this path exists and is writable by the container
        self.persistence_dir = os.path.join(BASE_DIR, "embeddings", "chromadb")
        
        # Ensure the directory exists
        os.makedirs(self.persistence_dir, exist_ok=True)
        logger.info(f"ChromaDB persistence directory: {self.persistence_dir}")
        
        try:
            # Use PersistentClient instead of Client for persistent storage
            self.client = chromadb.PersistentClient(path=self.persistence_dir)
            
            # Get or create the collection for filings embeddings
            self.collection = self.client.get_or_create_collection(
                name="filings_embeddings",
                metadata={"hnsw:space": "cosine"}
            )
            
            # Log the collection info
            count = self.collection.count()
            logger.info(f"ChromaDB collection 'filings_embeddings' initialized with {count} existing embeddings")
        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {e}", exc_info=True)
            raise

    def generate_embedding(self, text: str) -> list:
        try:
            # Truncate very long texts to prevent token limit issues
            max_chars = 8000
            if len(text) > max_chars:
                logger.info(f"Truncating text from {len(text)} to {max_chars} characters")
                text = text[:max_chars]
                
            embedding = self.model.encode(text).tolist()
            logger.info(f"Generated embedding for text (length: {len(text)} chars)")
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}", exc_info=True)
            return []

    def store_embedding(self, filing_id: str, text: str, metadata: dict = None):
        try:
            # Generate the embedding
            embedding = self.generate_embedding(text)
            
            if not embedding:
                logger.error(f"Failed to generate embedding for filing {filing_id}")
                return
            
            # Truncate text for document storage if needed
            max_chars = 8000
            document_text = text[:max_chars] if len(text) > max_chars else text
            
            # Add the embedding to the collection
            self.collection.add(
                documents=[document_text],
                ids=[str(filing_id)],  # Ensure ID is a string
                metadatas=[metadata or {}],
                embeddings=[embedding]
            )
            
            # Verify the embedding was stored
            count = self.collection.count()
            logger.info(f"Successfully stored embedding for filing {filing_id}. Collection now contains {count} embeddings.")
            
        except Exception as e:
            logger.error(f"Error storing embedding for filing {filing_id}: {e}", exc_info=True)