# SEC Filing Scanner

This project monitors and downloads SEC filings (10-K and 10-Q) for specified stock tickers using the sec-edgar-downloader package. It exposes a FastAPI API to report the scanner status and provides a Streamlit interface for interaction.

## Quick Start for Everyone

This guide will help you get the SEC Filing Scanner up and running, even if you have no technical background.

### What is this?
- This system automatically downloads financial filings (like 10-K and 10-Q reports) for big companies (Apple, Microsoft, etc.) from the SEC website.
- It processes these files, extracts important numbers (like revenue), and lets you ask questions about them in plain English.
- You get a simple website (Streamlit) to browse filings and ask questions, and a backend (API) that does all the heavy lifting.

### How do I start it?

**1. Make sure you have Docker installed.**
   - [Download Docker Desktop](https://www.docker.com/products/docker-desktop/) and install it if you don't have it.

**2. Open PowerShell in your project folder.**
   - Go to the folder where you see this README file.

**3. Start everything with one command:**

```powershell
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.streamlit.yml up --build -d
```

- This will automatically:
  - Download and process filings for you
  - Set up the database and all connections
  - Start the backend (API) and the website (Streamlit)

**4. Open your browser and go to:**
- [http://localhost:8501](http://localhost:8501) for the website (Streamlit)
- [http://localhost:8007](http://localhost:8007) for the backend API (for advanced users)

**5. To stop everything:**
```powershell
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.streamlit.yml down
```

---

### What happens when I start the system?
- The backend starts a scanner that looks for new filings and downloads them.
- It processes all filings it finds, extracts numbers, and saves them in a database.
- The website lets you browse filings, see extracted numbers, and ask questions (like "What was Apple's revenue in 2022?").
- All of this happens automatically—just wait a few minutes after starting for the first time.

### Do I need to run any other scripts?
- **No, not for normal use!**
- Only run `python scripts/update_db.py` or `python scripts/process_filings.py --force` if you are told to fix the database or want to reprocess everything from scratch.

---

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

## Production Deployment with Docker

For production, use Docker Compose to run both the backend (FastAPI) and frontend (Streamlit) services. This ensures all components are started, connected, and data is persisted.

### 1. Build and Start All Services

From your project root, run:

```powershell
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.streamlit.yml up --build -d
```

- This will build and start both backend and frontend containers.
- The Streamlit UI will be available at [http://localhost:8501](http://localhost:8501).
- The backend API will be available at [http://localhost:8007](http://localhost:8007).

### 2. Stop All Services

```powershell
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.streamlit.yml down
```

### 3. When to Use `update_db.py` or `process_filings.py`

- **You do NOT need to run these every time.**
- Use them only for:
  - Initial database setup or migration
  - Fixing missing metrics or schema issues
  - Forcing a full reprocessing of all filings

### 4. Summary Table

| Task                        | Command (Powershell)                                                                 | When to Use                |
|-----------------------------|--------------------------------------------------------------------------------------|----------------------------|
| Start all services (prod)   | `docker-compose -f docker/docker-compose.yml -f docker/docker-compose.streamlit.yml up --build -d` | Always (prod)              |
| Stop all services           | `docker-compose -f docker/docker-compose.yml -f docker/docker-compose.streamlit.yml down`           | When shutting down         |
| One-time DB fix/migration   | `python scripts/update_db.py`                                                        | Only for schema/migration  |
| Force reprocess all filings | `python scripts/process_filings.py --force`                                          | Only for full reprocessing |

---

## Running the Application

> **For production, use Docker Compose as described above.**

For local development, you can also run the backend and frontend separately:

1. **Start the FastAPI backend:**

   ```powershell
   uvicorn app.main:app --reload
   ```

2. **Start the Streamlit frontend:**

   ```powershell
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
