#!/bin/bash
echo "Starting FastAPI app..."
uvicorn app.main:app --reload
