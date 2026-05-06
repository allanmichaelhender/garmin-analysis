FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Set PYTHONPATH to include the app directory
ENV PYTHONPATH=/app

# Change to app directory before running
WORKDIR /app

# Run the application from the app directory
CMD ["python", "-m", "uvicorn", "mcp_server:app", "--host", "0.0.0.0", "--port", "8000"]
