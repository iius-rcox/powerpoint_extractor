FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y ffmpeg libreoffice && \
    rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy application source
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# Create non-root user
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /app

# Switch to non-root user
USER appuser

# Expose the HTTP port used by the application
EXPOSE 80

# Default command
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:80", "-c", "gunicorn.conf.py", "extractor_api:app"]
