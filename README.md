# SEC Filing Scanner

This project monitors and downloads SEC filings (10-K and 10-Q) for specified stock tickers using the sec-edgar-downloader package. It processes the filings to extract key financial metrics, stores them in SQLite, generates embeddings for semantic search, and provides a Streamlit UI for analysis and AI-powered chat.

## Milestone 1: SEC Raw Data Collection

- **Features:**
  - Monitor SEC filings for a set list of stock tickers.
  - Download filings automatically and store them in `data/filings/`.
  - Expose a FastAPI endpoint to check the scanner status.

## Setup

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
