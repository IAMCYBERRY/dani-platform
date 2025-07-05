# Multi-stage Dockerfile for HRIS Platform

# Stage 1: Build stage
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Production stage
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/venv/bin:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    postgresql-client \
    netcat-traditional \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Create app user
RUN addgroup --system app && adduser --system --group app

# Create directories
RUN mkdir -p /app/staticfiles /app/media /app/logs
WORKDIR /app

# Copy project files
COPY . /app/

# Set ownership and permissions
RUN chown -R app:app /app
RUN chmod +x /app/entrypoint.sh

# Switch to app user
USER app

# Expose port
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "hris_platform.wsgi:application"]