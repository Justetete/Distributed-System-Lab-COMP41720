FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY server.py client.py ./

# Create non-root user for security
RUN groupadd -r socketapp && useradd -r -g socketapp socketapp
RUN chown -R socketapp:socketapp /app
USER socketapp

# Expose port 8080
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import socket; s=socket.socket(); s.settimeout(1); s.connect(('localhost', 8080)); s.close()" || exit 1

# Default command
CMD ["python", "server.py", "--host", "0.0.0.0"]