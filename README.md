# SEC Filing Scanner

This project monitors and downloads SEC filings (10-K and 10-Q) for specified stock tickers using the sec-edgar-downloader package. It exposes a FastAPI API to report the scanner status and provides a Streamlit interface for interaction.

## Prerequisites

- Python 3.8+
- OpenAI API key for embeddings
- Chrome browser (recommended for Streamlit UI)
- SQLite3
- ChromaDB for vector storage

## Environment Setup

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   Create a `.env` file in the root directory with:

   ```
   OPENAI_API_KEY=your_openai_api_key
   SEC_EMAIL=your_email@domain.com
   ```

3. **Initialize the database:**

   ```bash
   python scripts/update_db.py
   ```

## Running the Application

1. **Start the FastAPI backend:**

   ```bash
   uvicorn app.main:app --reload
   ```

2. **Start the Streamlit frontend:**

   ```bash
   streamlit run streamlit_app.py
   ```

The application will:

- Start downloading SEC filings for configured tickers
- Process and store filings in SQLite database
- Generate embeddings for text search
- Make filings available through the Streamlit UI

## Core Features

- Real-time SEC filing monitoring
- Natural language querying of filing contents
- Financial metrics extraction and visualization
- Interactive chat interface with predefined questions
- Clear chat functionality
- Automated filing processing and embedding generation

## System Architecture

The system consists of several components:

- SEC Filing Scanner: Monitors and downloads new filings
- Processing Pipeline: Extracts and processes filing data
- Embedding Service: Generates and stores text embeddings
- SQLite Storage: Stores filing metadata and metrics
- Streamlit UI: Provides user interface for interaction

## Monitoring and Maintenance

The application includes comprehensive logging for monitoring:

- Scanner status and new filing downloads
- Processing pipeline operations
- Database operations
- Embedding generation
- API endpoints

Logs can be found in the application's standard output.

## Troubleshooting

If you encounter issues:

1. **Database Issues:**
   - Verify SQLite database exists in `data/db/sec_filings.db`
   - Run `python scripts/update_db.py` to reset the database

2. **Embedding Issues:**
   - Check OpenAI API key is set correctly
   - Verify ChromaDB files in `embeddings/chromadb/`

3. **Scanner Issues:**
   - Verify SEC email is configured correctly
   - Check network connectivity
   - Review logs for download errors
