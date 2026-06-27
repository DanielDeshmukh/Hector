#!/usr/bin/env bash
# HECTOR RAGAS Evaluation Runner
#
# Usage:
#   bash evaluation/run_eval.sh
#   bash evaluation/run_eval.sh --host localhost --port 8000
#   bash evaluation/run_eval.sh --top-k 20 --output-dir results/v2
#
# Requires:
#   - HECTOR API running at the target host:port
#   - Python 3.11+ with requests installed

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Defaults
HOST="${HECTOR_API_HOST:-localhost}"
PORT="${HECTOR_API_PORT:-8000}"
API_KEY="${HECTOR_API_KEY:-}"
TOP_K=10
OUTPUT_DIR="results"
EXTRA_ARGS=()

# Parse CLI args
while [[ $# -gt 0 ]]; do
    case "$1" in
        --host) HOST="$2"; shift 2 ;;
        --port) PORT="$2"; shift 2 ;;
        --api-key) API_KEY="$2"; shift 2 ;;
        --top-k) TOP_K="$2"; shift 2 ;;
        --output-dir) OUTPUT_DIR="$2"; shift 2 ;;
        *) EXTRA_ARGS+=("$1"); shift ;;
    esac
done

echo "============================================"
echo "  HECTOR RAGAS Evaluation"
echo "============================================"
echo "  Target: http://${HOST}:${PORT}"
echo "  Top-K:  ${TOP_K}"
echo "  Output: ${OUTPUT_DIR}"
echo "============================================"
echo ""

# Check if HECTOR is reachable
echo "Checking HECTOR API connectivity..."
if ! curl -s -o /dev/null -w "%{http_code}" "http://${HOST}:${PORT}/v1/healthz" 2>/dev/null | grep -qE '(200|401)'; then
    echo "WARNING: HECTOR API may not be reachable at http://${HOST}:${PORT}"
    echo "         Proceeding anyway (will report connection errors per query)..."
fi
echo ""

# Build command
CMD=(
    python "${SCRIPT_DIR}/evaluate_rag.py"
    --dataset-paths "${SCRIPT_DIR}"
    --host "${HOST}"
    --port "${PORT}"
    --top-k "${TOP_K}"
    --output-dir "${OUTPUT_DIR}"
)

if [[ -n "${API_KEY}" ]]; then
    CMD+=(--api-key "${API_KEY}")
fi

CMD+=("${EXTRA_ARGS[@]}")

# Run evaluation
echo "Running evaluation..."
"${CMD[@]}"

EXIT_CODE=$?

echo ""
if [[ $EXIT_CODE -eq 0 ]]; then
    echo "Evaluation completed successfully."
    echo "Results: ${OUTPUT_DIR}/rag_evaluation_summary.json"
else
    echo "Evaluation completed with warnings (exit code: ${EXIT_CODE})."
    echo "Check results for details."
fi

exit $EXIT_CODE
