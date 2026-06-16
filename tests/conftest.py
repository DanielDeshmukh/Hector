"""Shared test fixtures for HECTOR test suite."""

import os
import sys

import pytest
from fastapi.testclient import TestClient

# Ensure project root is on path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


@pytest.fixture(scope="session")
def project_root():
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def test_env():
    """Set test environment variables before any imports."""
    os.environ.setdefault("HECTOR_API_KEY", "test-api-key-for-testing-only")
    os.environ.setdefault(
        "HECTOR_JWT_SECRET", "test-jwt-secret-32-bytes-minimum-value!"
    )
    os.environ.setdefault(
        "HECTOR_DB_PATH", os.path.join(PROJECT_ROOT, "test_hector_db")
    )
    os.environ.setdefault(
        "HECTOR_BOOKS_DIR", os.path.join(PROJECT_ROOT, "data", "Books")
    )
    yield
    # Cleanup test DB
    import shutil

    test_db = os.path.join(PROJECT_ROOT, "test_hector_db")
    if os.path.exists(test_db):
        shutil.rmtree(test_db, ignore_errors=True)


@pytest.fixture(scope="session")
def api_client(test_env):
    """Create a TestClient for the FastAPI app."""
    from api.app import app

    client = TestClient(app)
    yield client


@pytest.fixture
def auth_headers():
    """Return headers with a valid API key."""
    return {"X-API-Key": "test-api-key-for-testing-only"}


@pytest.fixture
def auth_token(api_client, auth_headers):
    """Get a JWT token for authenticated requests."""
    resp = api_client.post("/auth/token?api_key=test-api-key-for-testing-only")
    if resp.status_code == 200:
        return {"Authorization": f"Bearer {resp.json()['access_token']}"}
    return auth_headers
