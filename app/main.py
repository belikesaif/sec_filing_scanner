import threading
import time
from fastapi import FastAPI
from app.utils.logger import setup_logger
from app.api.endpoints import filings, chatbot
from app.services.sec_scanner import SecFilingScanner
from app.services.processing_pipeline import ProcessingPipeline

logger = setup_logger(__name__)
app = FastAPI(title="SEC Filing Scanner API", version="0.1")

# Include API routes for filings status and chat endpoints
app.include_router(filings.router, prefix="/filings", tags=["filings"])
app.include_router(chatbot.router, prefix="/chatbot", tags=["chatbot"])

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
    while True:
        logger.info("Processing scheduler running: scanning for new filings...")
        processing_pipeline.process_all_new_filings()
        # Wait 5 minutes before the next scan
        time.sleep(3)

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
