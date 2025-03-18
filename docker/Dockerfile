# docker/Dockerfile
FROM python:3.9-slim

# Ensure output is flushed immediately
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Copy dependency file and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . .

# Expose port 8000
EXPOSE 8000

ENV PYTHONPATH=/app

# Command to run the FastAPI application using Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
