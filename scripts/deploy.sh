#!/usr/bin/env bash
# HECTOR Deployment Script
# Usage:
#   ./scripts/deploy.sh              # Deploy dev (API + Frontend)
#   ./scripts/deploy.sh --prod       # Deploy production (with Nginx, Redis, PostgreSQL)
#   ./scripts/deploy.sh --tools      # Run downloader/ingest tools

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEPLOY_MODE="${1:-dev}"

cd "$PROJECT_ROOT"

echo "============================================"
echo "  HECTOR Deployment"
echo "  Mode: $DEPLOY_MODE"
echo "  Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================"

# Pre-flight checks
echo ""
echo "[1/4] Pre-flight checks..."

if [ ! -f .env ]; then
    echo "ERROR: .env file not found."
    echo "Copy .env.example to .env and configure your API keys."
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed."
    exit 1
fi

if ! docker info &> /dev/null 2>&1; then
    echo "ERROR: Docker daemon is not running."
    exit 1
fi

echo "  OK: .env exists, Docker is running"

# Build images
echo ""
echo "[2/4] Building Docker images..."
if [ "$DEPLOY_MODE" = "--prod" ]; then
    docker compose -f docker-compose.prod.yml build
else
    docker compose build
fi

# Stop existing containers
echo ""
echo "[3/4] Stopping existing containers..."
if [ "$DEPLOY_MODE" = "--prod" ]; then
    docker compose -f docker-compose.prod.yml down
else
    docker compose --profile full down
fi

# Start services
echo ""
echo "[4/4] Starting services..."
if [ "$DEPLOY_MODE" = "--prod" ]; then
    docker compose -f docker-compose.prod.yml --env-file .env up -d
    echo ""
    echo "Production deployment complete."
    echo "  Frontend: https://your-domain.com"
    echo "  API:      https://your-domain.com/api"
    echo "  Nginx:    http://localhost:80"
elif [ "$DEPLOY_MODE" = "--tools" ]; then
    echo "Tools mode - use specific commands:"
    echo "  docker compose run downloader    # Download PDFs"
    echo "  docker compose run ingest        # Ingest books"
    echo "  docker compose run status        # Check status"
else
    docker compose --profile full up -d
    echo ""
    echo "Dev deployment complete."
    echo "  Frontend: http://localhost:3000"
    echo "  API:      http://localhost:8000"
    echo "  API Docs: http://localhost:8000/docs"
fi

# Health check
echo ""
echo "Waiting for API to be healthy..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:8000/healthz > /dev/null 2>&1; then
        echo "  API is healthy!"
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "  WARNING: API did not become healthy within 30 seconds."
        echo "  Check logs: docker compose logs api"
    fi
    sleep 1
done

echo ""
echo "Deployment finished at $(date '+%H:%M:%S')"
