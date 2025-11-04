FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY src/client_app.py .
COPY src/backend_client.py .
COPY src/config.py .

# Expose port 8080
EXPOSE 8080

# Environment variables with defaults
ENV BACKEND_URL=http://backend-service:5000
ENV CLIENT_PORT=8080
ENV CLIENT_HOST=0.0.0.0
ENV REQUEST_TIMEOUT=5
ENV DEBUG=False
ENV LOG_LEVEL=INFO

# Flask Configuration
ENV FLASK_APP=client_app.py
ENV FLASK_ENV=production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8080/health', timeout=5)"

# Run the application
CMD ["python", "client_app.py"]