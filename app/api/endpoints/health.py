from fastapi import APIRouter, HTTPException
from app.services.sql_storage import SQLStorage
from app.services.embedding import EmbeddingService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()

@router.get("/health")
async def check_health():
    """Check the health of all system components."""
    health_status = {
        "status": "healthy",
        "components": {
            "database": {"status": "healthy", "details": None},
            "embeddings": {"status": "healthy", "details": None},
        }
    }
    
    # Check database
    try:
        sql_storage = SQLStorage()
        # Try a simple query
        result = sql_storage.get_all_tickers()
        health_status["components"]["database"]["details"] = f"Connected, found {len(result)} tickers"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["components"]["database"]["status"] = "unhealthy"
        health_status["components"]["database"]["details"] = str(e)
        logger.error(f"Database health check failed: {e}")
    
    # Check embeddings
    try:
        embedding_service = EmbeddingService()
        # Try to access the collection
        collection_count = embedding_service.collection.count()
        health_status["components"]["embeddings"]["details"] = f"Connected, {collection_count} documents indexed"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["components"]["embeddings"]["status"] = "unhealthy"
        health_status["components"]["embeddings"]["details"] = str(e)
        logger.error(f"Embeddings health check failed: {e}")
    
    return health_status
