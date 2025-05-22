# SEC Filing Scanner System Architecture

## Overview

The SEC Filing Scanner is a comprehensive system that monitors, downloads, processes, and analyzes SEC filings (10-K and 10-Q) for specified stock tickers. The system provides a user-friendly interface for exploring financial data and interacting with an AI assistant to answer questions about the filings.

## System Components

### 1. Scheduler

The `FilingScheduler` class (in `app/services/scheduler.py`) is the central orchestrator of the system. It:

- Periodically polls for new SEC filings based on configured intervals
- Manages the downloading and processing of filings
- Implements idempotency checks to avoid duplicate processing
- Uses structured JSON logging for monitoring and debugging
- Handles errors gracefully with appropriate retry mechanisms

### 2. Downloader

The `SecFilingDownloader` class (in `app/services/downloader.py`) is responsible for:

- Downloading SEC filings using the sec-edgar-downloader package
- Handling connection errors and retries
- Logging download status and results

### 3. Processor

The `FilingProcessor` class (in `app/services/processor.py`) extracts valuable information from raw filings:

- Parses the full submission text to extract metadata
- Identifies and extracts key financial metrics (revenue, net income, etc.)
- Normalizes financial values for consistent analysis

### 4. Storage

The system uses two storage mechanisms:

- **SQLite Database** (`app/services/sql_storage.py`): Stores filing metadata and extracted metrics
- **ChromaDB Vector Database** (`app/services/embedding.py`): Stores text embeddings for semantic search

### 5. API Layer

The FastAPI backend (`app/main.py` and `app/api/endpoints/`) provides:

- Endpoints for filing status and metadata
- Chatbot functionality for querying filing data
- Debug endpoints for system monitoring

### 6. Streamlit UI

The Streamlit frontend (`frontend/Home.py` and `frontend/pages/`) offers:

- Dashboard for viewing key financial metrics
- Chat interface for interacting with the AI assistant
- Filing explorer for browsing raw documents
- System health monitoring panel

## Data Flow

1. The scheduler periodically triggers the downloader to check for new filings
2. Downloaded filings are processed to extract text and metrics
3. Extracted data is stored in SQLite and embeddings in ChromaDB
4. The Streamlit UI queries the backend API to display data and interact with the user

## Configuration System

The system uses a centralized configuration approach:

- `config.yaml` in the project root contains all system settings
- `app/utils/config_loader.py` provides a utility for loading and accessing config values
- Environment variables can override config values for deployment flexibility

## Improvements Made

### 1. Centralized Configuration

- Created a unified `config.yaml` file to replace scattered configuration
- Implemented a `ConfigLoader` utility for consistent config access

### 2. Enhanced Scheduler

- Replaced the basic processing_scheduler with a robust `FilingScheduler` class
- Added idempotency checks to prevent duplicate processing
- Implemented structured JSON logging for better monitoring

### 3. Streamlit UI Enhancements

- Added a health check panel to monitor system components
- Fixed missing imports in Home.py
- Improved error handling and user feedback

### 4. Testing Infrastructure

- Created end-to-end tests to validate the complete pipeline
- Implemented mock objects for testing without external dependencies

### 5. CI/CD Pipeline

- Added GitHub Actions workflow for automated testing and deployment
- Configured linting, testing, and Docker build steps

## Future Improvements

1. **Metadata Table**: Create a dedicated table for scheduler metadata to track last run timestamps
2. **Retry Mechanism**: Enhance the retry logic for failed downloads and processing
3. **Monitoring Dashboard**: Expand the health check panel into a full monitoring dashboard
4. **User Authentication**: Add user authentication for multi-user deployments
5. **Advanced Analytics**: Implement trend analysis and anomaly detection for financial metrics