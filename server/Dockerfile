FROM python:3.11-slim

# Install system dependencies that might be needed
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Pathway and related packages
RUN pip install pathway unstructured tiktoken openai langchain

# Copy application code
COPY . .

# Expose port if needed
EXPOSE 8000

# Default command
CMD ["python", "main.py"]
