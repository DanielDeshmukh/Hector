"""Entry point for the `hector` command (see .venv/Scripts/hector.* shims)."""
from __future__ import annotations

import os
import sys

API_DIR = os.path.dirname(os.path.abspath(__file__))


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    os.chdir(API_DIR)
    if API_DIR not in sys.path:
        sys.path.insert(0, API_DIR)
    from core.cli import main as cli_main

    cli_main()


if __name__ == "__main__":
    main()
