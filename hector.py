#!/usr/bin/env python
"""Direct Python entrypoint for the HECTOR CLI."""
import os
import sys

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_DIR)
sys.path.insert(0, PROJECT_DIR)

sys.argv[0] = 'hector'
import main  # noqa: E402
main.main()
