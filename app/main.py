import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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

# Import required components
from app.services.scheduler import FilingScheduler
from app.api.endpoints import status

# Include API routes
app.include_router(status.router, tags=["status"])

# Instantiate the Filing Scheduler (handles both downloading and processing)
filing_scheduler = FilingScheduler()

@app.on_event("startup")
async def startup_event():
    logger.info("Application startup: starting SEC Filing Scheduler")
    # Start the filing scheduler which handles both downloading and processing
    filing_scheduler.start()


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown: stopping SEC Filing Scheduler")
    filing_scheduler.stop()

@app.get("/")
async def root():
    return {"message": "Welcome to the SEC Filing Scanner API"}
