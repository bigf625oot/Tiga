# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
# build-essential: for compiling some python packages
# libpq-dev: for PostgreSQL (if used via psycopg2)
# curl: for healthchecks or downloading files
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Create directory for uploads/storage as expected by app/main.py
RUN mkdir -p data/storage

# Expose port 8000
EXPOSE 8000

# Command to run the application using uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
