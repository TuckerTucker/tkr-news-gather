# Use Python 3.9 slim image with security updates (explicitly specify amd64 for RunPod compatibility)
FROM --platform=linux/amd64 python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies with security updates
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first for better caching
COPY requirements.txt .

# Upgrade pip and install Python dependencies with security focus
RUN python -m pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --upgrade -r requirements.txt

# Install Playwright system dependencies as root (after Playwright is installed)
RUN playwright install-deps

# Copy source code
COPY src/ ./src/
COPY database/ ./database/
COPY runpod_handler.py .
COPY runpod_wrapper.py .

# Create a non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Install Playwright browsers as the appuser
RUN playwright install chromium

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Default command - RunPod handler with auto-detection
CMD ["python", "runpod_handler.py"]