#!/bin/bash
# SEC Filing Scanner - Unix Setup Launcher
# This script provides an easy way to run the setup on Unix-based systems

echo "========================================"
echo "SEC Filing Scanner - Setup Launcher"
echo "========================================"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "ERROR: Python is not installed or not in PATH"
        echo "Please install Python 3.8-3.11"
        echo "Ubuntu/Debian: sudo apt-get install python3"
        echo "macOS: brew install python3"
        echo "CentOS/RHEL: sudo yum install python3"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

echo "Python found. Starting setup launcher..."
echo

# Run the Python setup launcher
$PYTHON_CMD setup_launcher.py

# Check if setup was successful
if [ $? -eq 0 ]; then
    echo
    echo "========================================"
    echo "Setup process completed"
    echo "========================================"
    echo
    echo "To run the application:"
    echo "1. Backend: uvicorn app.main:app --reload"
    echo "2. Frontend: streamlit run streamlit_app.py"
    echo
else
    echo
    echo "========================================"
    echo "Setup encountered issues"
    echo "========================================"
    echo
    echo "Please check the error messages above"
    echo "and refer to SETUP_README.md for help"
    echo
fi

read -p "Press Enter to continue..."
