# SEC Filing Scanner - Complete Setup Guide

Welcome! This guide will help you set up the SEC Filing Scanner on your system with minimal effort. We've created several automated setup scripts to handle different scenarios and ensure everything works correctly.

## 🚀 Quick Start (Recommended)

For most users, start here:

```powershell
# 1. Clone/download the project
# 2. Navigate to the project directory
cd "SEC Filing Scanner\sec_filing_scanner"

# 3. Run the comprehensive setup (this handles everything)
python comprehensive_setup.py
```

## 📋 System Requirements

- **Python**: 3.8 to 3.11 (Python 3.12+ may have compatibility issues)
- **Operating System**: Windows, macOS, or Linux
- **Memory**: At least 4GB RAM (8GB recommended for ML operations)
- **Storage**: At least 2GB free space
- **Internet**: Required for downloading dependencies and SEC filings

## 🛠️ Setup Scripts Overview

We provide three different setup scripts for different needs:

### 1. `comprehensive_setup.py` - **RECOMMENDED**
**Best for: First-time setup, complete environment validation**

This is our most thorough setup script that:
- ✅ Checks system requirements
- ✅ Creates fixed requirements with compatible versions
- ✅ Installs dependencies in stages to avoid conflicts
- ✅ Validates all imports work correctly
- ✅ Tests application components
- ✅ Checks environment configuration
- ✅ Sets up required directories
- ✅ Runs functionality tests
- ✅ Only proceeds when ALL requirements are satisfied

```powershell
python comprehensive_setup.py
```

### 2. `setup_and_check.py` - **DIAGNOSTIC**
**Best for: Troubleshooting, dependency analysis**

This script focuses on dependency analysis and diagnostics:
- 🔍 Analyzes current Python environment
- 🔍 Identifies missing packages
- 🔍 Detects version conflicts
- 🔍 Provides detailed diagnostics
- 🔍 Suggests specific fixes

```powershell
python setup_and_check.py
```

### 3. `debug_and_fix.py` - **REPAIR**
**Best for: Fixing specific database/application issues**

This script repairs common application issues:
- 🔧 Ensures directories exist
- 🔧 Verifies database connections
- 🔧 Tests core services
- 🔧 Fixes embedding issues

```powershell
python debug_and_fix.py
```

## 📁 Step-by-Step Setup Process

### Step 1: Prepare Your Environment

1. **Install Python** (if not already installed):
   - Download from [python.org](https://www.python.org/downloads/)
   - Choose version 3.8-3.11 (avoid 3.12+ for now)
   - During installation, check "Add Python to PATH"

2. **Verify Python installation**:
   ```powershell
   python --version
   pip --version
   ```

3. **Create a virtual environment** (recommended):
   ```powershell
   python -m venv venv
   venv\Scripts\activate  # On Windows
   # source venv/bin/activate  # On macOS/Linux
   ```

### Step 2: Run the Setup

1. **Navigate to the project directory**:
   ```powershell
   cd "path\to\SEC Filing Scanner\sec_filing_scanner"
   ```

2. **Run the comprehensive setup**:
   ```powershell
   python comprehensive_setup.py
   ```

3. **Follow the setup output**:
   - The script will show progress for each phase
   - ✅ Green checkmarks indicate success
   - ❌ Red X marks indicate issues that need attention
   - ⚠️ Yellow warnings are usually non-critical

### Step 3: Environment Configuration

1. **Create a `.env` file** in the project root:
   ```powershell
   # Copy the example or create new
   copy .env.example .env  # If example exists
   # Or create manually
   ```

2. **Edit the `.env` file** with your settings:
   ```
   # Required
   OPENAI_API_KEY=your_openai_api_key_here
   SEC_EMAIL=your.email@example.com

   # Optional
   FILINGS_DIR=./sec-edgar-filings
   DATABASE_URL=sqlite:///./data/db/sec_filings.db
   ```

3. **Get your OpenAI API key**:
   - Visit [OpenAI API Keys](https://platform.openai.com/api-keys)
   - Create a new secret key
   - Add it to your `.env` file

### Step 4: Verify Installation

After setup completion, verify everything works:

```powershell
# Test the FastAPI backend
uvicorn app.main:app --reload

# In another terminal, test the Streamlit frontend
streamlit run streamlit_app.py
```

## 🐳 Alternative: Docker Setup

If you prefer using Docker:

```powershell
# Build and run with Docker Compose
docker-compose -f docker/docker-compose.yml up --build
```

This will start both the FastAPI backend and Streamlit frontend automatically.

## 🔧 Troubleshooting Guide

### Common Issues and Solutions

#### Issue: "Module not found" errors
**Solution:**
```powershell
# Run the diagnostic script
python setup_and_check.py

# Then run comprehensive setup again
python comprehensive_setup.py
```

#### Issue: Python version compatibility
**Symptoms:** Package installation failures, import errors
**Solution:**
- Use Python 3.8-3.11
- Avoid Python 3.12+ for now due to some package incompatibilities

#### Issue: PyTorch installation problems
**Solution:**
```powershell
# Install PyTorch separately first
pip install torch==2.6.0 --index-url https://download.pytorch.org/whl/cpu

# Then run setup again
python comprehensive_setup.py
```

#### Issue: ChromaDB installation problems
**Solution:**
```powershell
# Install build tools (Windows)
# Download and install Microsoft C++ Build Tools

# Or use conda instead of pip
conda install chromadb
```

#### Issue: Environment variables not working
**Solution:**
- Ensure `.env` file is in the project root
- Check file permissions
- Restart your terminal after creating `.env`

#### Issue: Database connection errors
**Solution:**
```powershell
# Run the debug script
python debug_and_fix.py
```

### Getting Detailed Diagnostics

For comprehensive diagnostics:

```powershell
# Run diagnostic script with verbose output
python setup_and_check.py --verbose

# Check specific components
python debug_and_fix.py --test-all
```

## 📊 Understanding Setup Output

The setup scripts use color-coded output:

- 🟢 **GREEN**: Success - everything is working correctly
- 🔴 **RED**: Error - requires immediate attention
- 🟡 **YELLOW**: Warning - may need attention but not critical
- 🔵 **BLUE**: Info - general information messages

### Setup Phases Explained

1. **System Requirements Check**: Validates Python version, pip availability
2. **Requirements Analysis**: Creates compatible dependency versions
3. **Dependency Installation**: Installs packages in stages to avoid conflicts
4. **Import Validation**: Tests that all critical packages can be imported
5. **Application Testing**: Verifies application components work
6. **Environment Check**: Validates configuration and environment variables
7. **Directory Setup**: Creates required directories
8. **Functionality Tests**: Tests core application features

## 🏃‍♂️ Running the Application

Once setup is complete:

### Option 1: FastAPI + Streamlit (Recommended)
```powershell
# Terminal 1: Start FastAPI backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start Streamlit frontend
streamlit run streamlit_app.py --server.port 8501
```

### Option 2: Docker Compose
```powershell
docker-compose -f docker/docker-compose.yml up
```

### Option 3: Individual Services
```powershell
# Just run the Streamlit app (includes embedded FastAPI)
streamlit run streamlit_app.py
```

## 🔍 Accessing the Application

- **Streamlit Frontend**: http://localhost:8501
- **FastAPI Backend**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📝 Configuration Options

### Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `OPENAI_API_KEY` | Yes | Your OpenAI API key | `sk-...` |
| `SEC_EMAIL` | Yes | Email for SEC API requests | `user@example.com` |
| `FILINGS_DIR` | No | Directory for SEC filings | `./sec-edgar-filings` |
| `DATABASE_URL` | No | Database connection string | `sqlite:///./data/db/sec_filings.db` |
| `EMBEDDING_MODEL` | No | OpenAI embedding model | `text-embedding-3-small` |
| `CHAT_MODEL` | No | OpenAI chat model | `gpt-4o-mini` |

### Application Settings

Edit `app/core/config.py` to customize:
- Company tickers to monitor
- Filing types to download
- Processing schedules
- Database settings

## 🆘 Getting Help

If you encounter issues:

1. **Check the logs**: Look for error messages in the terminal output
2. **Run diagnostics**: Use `python setup_and_check.py` for detailed analysis
3. **Check dependencies**: Ensure all required packages are installed
4. **Verify environment**: Make sure `.env` file is properly configured
5. **Review requirements**: Ensure your system meets minimum requirements

### Script Options

Each setup script supports additional options:

```powershell
# Get help for any script
python comprehensive_setup.py --help
python setup_and_check.py --help
python debug_and_fix.py --help

# Run with verbose output
python setup_and_check.py --verbose

# Test specific components
python debug_and_fix.py --test-database
python debug_and_fix.py --test-embeddings
```

## 🔄 Updating the Application

To update dependencies or fix issues:

```powershell
# Update all packages
pip install --upgrade -r requirements.txt

# Or run the comprehensive setup again
python comprehensive_setup.py
```

## 📚 Additional Resources

- **Project Documentation**: See `docs/` directory
- **API Documentation**: Visit http://localhost:8000/docs when running
- **Architecture Overview**: See `docs/architecture.md`
- **Docker Setup**: See `docker/` directory for containerized deployment

---

## ✅ Setup Checklist

Use this checklist to ensure complete setup:

- [ ] Python 3.8-3.11 installed
- [ ] Virtual environment created and activated
- [ ] Comprehensive setup script completed successfully
- [ ] `.env` file created with required variables
- [ ] OpenAI API key configured
- [ ] SEC email configured
- [ ] Application starts without errors
- [ ] Can access Streamlit frontend
- [ ] Can access FastAPI backend
- [ ] Database connections working
- [ ] Can scan and process SEC filings

**🎉 Congratulations! Your SEC Filing Scanner is ready to use!**

For any issues, run the diagnostic script and check the troubleshooting section above.
