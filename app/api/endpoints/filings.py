# app/api/endpoints/filings.py
from fastapi import APIRouter
from app.utils.logger import setup_logger
#=====================================================================================================================================================
logger = setup_logger(__name__)
router = APIRouter()
#=====================================================================================================================================================
@router.get("/status")
async def get_status():
    return {
        "status": "SEC Filing Scanner is running",
        "info": "Filings are being polled and downloaded as available."
    }
#=====================================================================================================================================================
@router.get("/debug/embeddings")
async def debug_embeddings():
    """Debug endpoint to check the state of embeddings in ChromaDB"""
    try:
        from app.services.embedding import EmbeddingService
        embedding_service = EmbeddingService()
        
        # Get collection info
        count = embedding_service.collection.count()
        peek = None
        if count > 0:
            peek = embedding_service.collection.peek(10)
        
        return {
            "status": "success",
            "collection_info": {
                "count": count,
                "sample_ids": peek["ids"] if peek else [],
                "embedding_dimensions": len(embedding_service.generate_embedding("test text")),
                "persistence_path": embedding_service.persistence_dir
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }