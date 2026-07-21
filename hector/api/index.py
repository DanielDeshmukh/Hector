"""Vercel serverless entry point for HECTOR FastAPI app."""
import sys
import os

here = os.path.dirname(os.path.abspath(__file__))
if here not in sys.path:
    sys.path.insert(0, here)

from api.app import app  # noqa: E402
