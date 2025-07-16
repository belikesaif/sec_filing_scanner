import os
from typing import Dict, Any, List
from app.utils.logger import setup_logger
import chromadb
from chromadb.utils import embedding_functions
from chromadb.config import Settings

logger = setup_logger(__name__)

class EmbeddingService:
    def __init__(self):
        try:
            # Use persistent storage
            self.client = chromadb.PersistentClient(path="./chroma_db")
            logger.info("Successfully initialized ChromaDB with persistent storage")
              # Use OpenAI embeddings
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is not set")
            
            # Set CHROMA_OPENAI_API_KEY for ChromaDB
            os.environ["CHROMA_OPENAI_API_KEY"] = api_key
            
            self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
                api_key=api_key,
                model_name="text-embedding-ada-002"
            )
            
            # Get or create the collection
            self.collection = self.client.get_or_create_collection(
                name="sec_filings",
                embedding_function=self.embedding_function
            )
            logger.info("Successfully initialized or retrieved collection 'sec_filings'")
            
        except Exception as e:
            logger.error(f"Failed to initialize EmbeddingService: {str(e)}")
            raise


    def chunk_text(self, text: str, chunk_size: int = 100000) -> List[str]:
        """Split text into chunks that fit within token limits."""
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            # Rough estimate: 1 word ≈ 1.3 tokens on average
            word_length = len(word) * 1.3
            if current_length + word_length > chunk_size:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_length = word_length
            else:
                current_chunk.append(word)
                current_length += word_length
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks

    def store_embedding(self, id: str, text: str, metadata: Dict[str, Any]) -> bool:
        """Store text embeddings in the database with error handling and logging."""
        try:
            # Split text into manageable chunks
            chunks = self.chunk_text(text)
            
            # Store each chunk with a unique ID
            for i, chunk in enumerate(chunks):
                chunk_id = f"{id}_chunk_{i}"
                chunk_metadata = metadata.copy()
                chunk_metadata["parent_id"] = id
                chunk_metadata["chunk_index"] = i
                chunk_metadata["total_chunks"] = len(chunks)
                
            try:
                existing = self.collection.get(ids=[chunk_id])
                if existing and existing['ids']:
                    logger.info(f"Chunk {chunk_id} already exists, updating...")
                    self.collection.update(
                        ids=[chunk_id],
                        documents=[chunk],
                        metadatas=[chunk_metadata]
                    )
                else:
                    self.collection.add(
                        documents=[chunk],
                        metadatas=[chunk_metadata],
                        ids=[chunk_id]
                    )
            except Exception as e:
                # If get fails, try adding
                logger.warning(f"Get operation failed for {id}, attempting add: {str(e)}")
                self.collection.add(
                    documents=[text],
                    metadatas=[metadata],
                    ids=[id]
                )
                
            logger.info(f"Successfully stored/updated embeddings for document {id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store embeddings for document {id}: {str(e)}")
            return False
    
    def query_similar(self, query_text: str, n_results: int = 5) -> dict:
        """Query similar documents with error handling and logging."""
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results
            )
            
            logger.info(f"Successfully queried similar documents for: {query_text[:100]}...")
            return results
            
        except Exception as e:
            logger.error(f"Failed to query similar documents: {str(e)}")
            return {"documents": [], "metadatas": [], "distances": []}
    
    def generate_embedding(self, text: str) -> str:
        """Generate embedding for a text string using the OpenAI embedding function."""
        try:
            # Since we're using ChromaDB with OpenAI embeddings, we don't need to generate them manually
            # Just return the text and let ChromaDB handle the embedding
            return text
        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            return None