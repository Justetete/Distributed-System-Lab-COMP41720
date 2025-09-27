# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Create a non-root user for security
RUN groupadd -r socketuser && useradd -r -g socketuser socketuser

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies (if any)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY server.py client.py test_suite.py ./

# Change ownership of files to non-root user
RUN chown -R socketuser:socketuser /app

# Switch to non-root user
USER socketuser

# Expose the port the server will run on
EXPOSE 8080

# Health check to ensure server is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python client.py "health check" || exit 1

# Default command to run the server
CMD ["python", "server.py"]

# Alternative commands:
# To run client: docker run <image> python client.py
# To run tests: docker run <image> python test_suite.py
# To run interactive client: docker run -it <image> python client.py