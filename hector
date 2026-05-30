#!/bin/bash
# HECTOR CLI Wrapper - Universal entry point for all platforms
# Usage: hector <command> [options]
# Works in bash, MINGW64, and other shells

set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$SCRIPT_DIR"

# Activate venv
if [ -f "$PROJECT_DIR/venv/Scripts/activate" ]; then
    source "$PROJECT_DIR/venv/Scripts/activate"
elif [ -f "$PROJECT_DIR/venv/bin/activate" ]; then
    source "$PROJECT_DIR/venv/bin/activate"
else
    echo "[X] Virtual environment not found. Run 'python -m venv venv' first."
    exit 1
fi

# Run the main.py with all arguments
cd "$PROJECT_DIR"
python main.py "$@"
