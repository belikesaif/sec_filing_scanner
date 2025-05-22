import os
from typing import List, Dict
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

    def _split_text(self, text: str, max_length: int = 1000) -> List[str]:
        """Split text into chunks of approximately max_length characters."""
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            word_length = len(word)
            if current_length + word_length + 1 <= max_length:
                current_chunk.append(word)
                current_length += word_length + 1
            else:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_length = word_length
                
        if current_chunk:
            chunks.append(" ".join(current_chunk))
            
        return chunks

    def process_filing(self, filing_id: int, content: str) -> bool:
        """Process and store embeddings for a filing document."""
        try:
            # Split content into manageable chunks
            chunks = self._split_text(content)
            if not chunks:
                logger.warning(f"No content chunks generated for filing {filing_id}")
                return False

            # Generate embeddings for all chunks
            embeddings = []
            for chunk in chunks:
                embedding = self.generate_embedding(chunk)
                if not embedding:
                    logger.error(f"Failed to generate embedding for a chunk in filing {filing_id}")
                    return False
                embeddings.append(embedding)

            # Create document IDs for each chunk
            doc_ids = [f"filing_{filing_id}_chunk_{i}" for i in range(len(chunks))]
            metadatas = [{"filing_id": filing_id, "chunk_id": i, "total_chunks": len(chunks)} 
                        for i in range(len(chunks))]

            # Store embeddings with metadata
            self.collection.add(
                documents=chunks,
                embeddings=embeddings,
                ids=doc_ids,
                metadatas=metadatas
            )
            
            logger.info(f"Successfully processed embeddings for filing {filing_id} ({len(chunks)} chunks)")
            return True
            
        except Exception as e:
            logger.error(f"Error processing embeddings for filing {filing_id}: {e}", exc_info=True)
            return False

    def search(self, query: str, limit: int = 5) -> List[Dict]:
        """Search for similar content in embeddings."""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=limit
            )
            
            return [
                {
                    "text": doc,
                    "metadata": metadata,
                    "distance": distance
                }
                for doc, metadata, distance in zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0]
                )
            ]
            
        except Exception as e:
            logger.error(f"Error searching embeddings: {e}")
            return []