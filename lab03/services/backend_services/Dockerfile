FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY src/app.py .
COPY src/models.py .
COPY src/fault_injector.py .
COPY src/users.json .

# Expose port 5000
EXPOSE 5000

# Environment variables with defaults
# Fault Injection Configuration
ENV FAULT_INJECTION_ENABLED=true
ENV FAULT_DELAY_RATE=0.3
ENV FAULT_ERROR_RATE=0.2
ENV FAULT_TIMEOUT_RATE=0.1
ENV FAULT_MIN_DELAY=1.0
ENV FAULT_MAX_DELAY=5.0
ENV FAULT_TIMEOUT_DELAY=30.0

# Flask Configuration
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:5000/health', timeout=5)"

# Run the application
CMD ["python", "app.py"]