# HECTOR - Legal Intelligence System
# Multi-stage Docker build

# ── Stage 1: Base Python ──────────────────────────────────────────────
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps for PDF processing and OCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── Stage 2: Python Dependencies ─────────────────────────────────────
FROM base AS deps

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Stage 3: Application ─────────────────────────────────────────────
FROM deps AS app

# Copy application code
COPY api/ api/
COPY core/ core/
COPY data/ data/
COPY utils/ utils/
COPY scripts/ scripts/
COPY main.py .
COPY setup.py .
COPY .env.example .env

# Create directories
RUN mkdir -p hector_db data/Books .hector_logs

# Non-root user
RUN useradd -m -r hector && chown -R hector:hector /app
USER hector

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -sf http://localhost:8000/status || exit 1

EXPOSE 8000

# Default: start API server
CMD ["python", "-m", "uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
