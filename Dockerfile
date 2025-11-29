# Multi-stage build for optimized production image

# Stage 1: Builder
FROM python:3.14-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.14-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    postgresql-client \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 elibrary

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/elibrary/.local
ENV PATH=/home/elibrary/.local/bin:$PATH

# Copy application code
COPY --chown=elibrary:elibrary . .

# Create directories for static/media files
RUN mkdir -p /app/static /app/media && chown -R elibrary:elibrary /app

# Switch to non-root user
USER elibrary

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -m http.client localhost:8000 /health || exit 1

# Expose port
EXPOSE 8000

# Default command (override with gunicorn in production)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
