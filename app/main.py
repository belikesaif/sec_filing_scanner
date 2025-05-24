import os
import threading
import time
from fastapi import FastAPI
from dotenv import load_dotenv
from app.utils.logger import setup_logger

# Initialize environment and logging before any other imports
def init_environment():
    # Look for .env file in project root and parent directories
    env_path = None
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    while current_dir:
        test_path = os.path.join(current_dir, '.env')
        if os.path.exists(test_path):
            env_path = test_path
            break
        parent = os.path.dirname(current_dir)
        if parent == current_dir:
            break
        current_dir = parent
    
    # Load environment variables
    if env_path:
        logger.info(f"Loading environment variables from {env_path}")
        load_dotenv(env_path)
    else:
        logger.warning("No .env file found in project directory tree")
    
    # Verify critical environment variables
    required_vars = ["OPENAI_API_KEY", "SEC_EMAIL"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

logger = setup_logger(__name__)

# Initialize environment before any other imports
try:
    init_environment()
except Exception as e:
    logger.error(f"Failed to initialize environment: {e}")
    raise

# Create the FastAPI application
app = FastAPI(title="SEC Filing Scanner API", version="0.1")

# Import all required modules after environment is initialized
from app.services.sec_scanner import SecFilingScanner
from app.services.processing_pipeline import ProcessingPipeline

# Import and include API routes
from app.api.endpoints import filings
app.include_router(filings.router, prefix="/filings", tags=["filings"])

from app.api.endpoints import chatbot
app.include_router(chatbot.router, prefix="/chatbot", tags=["chatbot"])

from app.api.endpoints import health
app.include_router(health.router, prefix="/system", tags=["system"])

# Include API routes for filings status and chat endpoints
app.include_router(filings.router, prefix="/filings", tags=["filings"])
app.include_router(chatbot.router, prefix="/chatbot", tags=["chatbot"])
app.include_router(health.router, prefix="/system", tags=["system"])

# Instantiate the SEC scanner (downloads filings continuously)
scanner = SecFilingScanner()

# Instantiate the Processing Pipeline (processes and indexes downloaded filings)
processing_pipeline = ProcessingPipeline()

def processing_scheduler():
    """
    Background task that periodically scans the 'sec-edgar-filings' directory for new filings.
    For each new filing (identified by its unique file path), it calls process_and_store() to process,
    extract data, store the filing in SQLite, and generate embeddings in ChromaDB.
    """
    last_run = None
    error_count = 0
    max_errors = 3  # Reset error count after 3 successful runs
    
    while True:
        try:
            current_time = time.strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"Processing scheduler running at {current_time}. Last run: {last_run}")
            
            processing_pipeline.process_all_new_filings()
            
            last_run = current_time
            if error_count > 0:
                error_count -= 1  # Decrease error count on successful run
                logger.info(f"Error count decreased to {error_count}")
                
            time.sleep(300)  # Sleep for 5 minutes
            
        except Exception as e:
            error_count += 1
            logger.error(f"Error in processing scheduler: {str(e)}")
            if error_count >= max_errors:
                logger.critical(f"Processing scheduler has encountered {error_count} consecutive errors. Continuing but needs attention.")
            time.sleep(60)  # Sleep for 1 minute on error before retrying

@app.on_event("startup")
async def startup_event():
    logger.info("Application startup: starting SEC Filing Scanner")
    scanner.start()
    # Immediately process any existing files
    processing_pipeline.process_all_new_filings()
    # Launch the processing scheduler in a background thread for continuous checking
    processing_thread = threading.Thread(target=processing_scheduler, daemon=True)
    processing_thread.start()


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown: stopping SEC Filing Scanner")
    scanner.stop()

@app.get("/")
async def root():
    return {"message": "Welcome to the SEC Filing Scanner API"}
