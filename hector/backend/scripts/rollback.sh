#!/usr/bin/env bash
# HECTOR Rollback Script
# Usage:
#   ./scripts/rollback.sh              # Roll back to previous Docker image
#   ./scripts/rollback.sh --git        # Roll back to previous git commit
#   ./scripts/rollback.sh --db         # Roll back ChromaDB to last backup

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ROLLBACK_MODE="${1:-docker}"

cd "$PROJECT_ROOT"

echo "============================================"
echo "  HECTOR Rollback"
echo "  Mode: $ROLLBACK_MODE"
echo "  Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================"

case "$ROLLBACK_MODE" in
    --git)
        echo ""
        echo "Rolling back to previous git commit..."
        
        # Check for uncommitted changes
        if ! git diff --quiet HEAD 2>/dev/null; then
            echo "WARNING: You have uncommitted changes."
            read -p "Stash changes before rollback? (y/n): " stash
            if [ "$stash" = "y" ]; then
                git stash push -m "rollback-$(date +%s)"
                echo "  Changes stashed."
            fi
        fi
        
        # Get previous commit
        PREV_COMMIT=$(git rev-parse HEAD~1)
        echo "  Current:  $(git rev-parse --short HEAD)"
        echo "  Rolling to: $(git rev-parse --short $PREV_COMMIT)"
        
        read -p "Confirm rollback? (y/n): " confirm
        if [ "$confirm" = "y" ]; then
            git checkout "$PREV_COMMIT"
            echo "  Rolled back to $PREV_COMMIT"
            echo "  Run ./scripts/deploy.sh to redeploy."
        else
            echo "  Rollback cancelled."
        fi
        ;;
        
    --db)
        echo ""
        echo "Rolling back ChromaDB to last backup..."
        
        DB_PATH="${HECTOR_DB_PATH:-./hector_db}"
        BACKUP_DIR="$DB_PATH/backups"
        
        if [ ! -d "$BACKUP_DIR" ]; then
            echo "ERROR: No backup directory found at $BACKUP_DIR"
            echo "Create a backup first: ./scripts/backup-db.sh"
            exit 1
        fi
        
        LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/*.tar.gz 2>/dev/null | head -1)
        
        if [ -z "$LATEST_BACKUP" ]; then
            echo "ERROR: No backup files found in $BACKUP_DIR"
            exit 1
        fi
        
        echo "  Latest backup: $(basename "$LATEST_BACKUP")"
        echo "  Backup date: $(stat -c %y "$LATEST_BACKUP" 2>/dev/null || stat -f %Sm "$LATEST_BACKUP")"
        
        read -p "Confirm restore? This will overwrite current database. (y/n): " confirm
        if [ "$confirm" = "y" ]; then
            # Stop API first
            docker compose stop api 2>/dev/null || true
            
            # Restore
            tar -xzf "$LATEST_BACKUP" -C "$DB_PATH"
            
            # Restart API
            docker compose start api 2>/dev/null || true
            
            echo "  Database restored from $(basename "$LATEST_BACKUP")"
        else
            echo "  Restore cancelled."
        fi
        ;;
        
    *)
        echo ""
        echo "Rolling back Docker containers to previous image..."
        
        # Find previous image
        CURRENT_IMAGE=$(docker inspect hector-api --format='{{.Image}}' 2>/dev/null || echo "")
        
        if [ -z "$CURRENT_IMAGE" ]; then
            echo "ERROR: No running hector-api container found."
            echo "Run ./scripts/deploy.sh first."
            exit 1
        fi
        
        # List available images
        echo "Available hector-api images:"
        docker images hector-api --format "  {{.ID}} {{.CreatedAt}} {{.Tag}}" | head -5
        
        echo ""
        echo "To roll back, specify the image tag:"
        echo "  docker compose up -d api --force-recreate"
        echo ""
        echo "Or use git rollback: ./scripts/rollback.sh --git"
        ;;
esac

echo ""
echo "Rollback finished at $(date '+%H:%M:%S')"
