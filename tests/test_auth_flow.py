"""
Tests for authentication flow: JWT generation, validation, expiration, and security.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.security import auth_manager


class TestAuthManager:
    """Tests for the AuthManager class."""

    def test_api_key_stored(self):
        assert auth_manager.api_key is not None
        assert len(auth_manager.api_key) > 10

    def test_verify_correct_key(self):
        assert auth_manager.verify_api_key(auth_manager.api_key) is True

    def test_verify_wrong_key(self):
        assert auth_manager.verify_api_key("wrong-key-here") is False

    def test_verify_empty_key(self):
        assert auth_manager.verify_api_key("") is False

    def test_verify_none_key(self):
        assert auth_manager.verify_api_key(None) is False

    def test_issue_token(self):
        token = auth_manager.issue_token()
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 20
        assert token.count(".") == 2

    def test_issue_token_custom_subject(self):
        token = auth_manager.issue_token(subject="test-client")
        assert token is not None

    def test_verify_token_valid(self):
        token = auth_manager.issue_token(subject="test-verify")
        payload = auth_manager.verify_token(token)
        assert payload is not None
        assert "exp" in payload
        assert "sub" in payload
        assert payload["sub"] == "test-verify"

    def test_verify_token_invalid_format(self):
        with pytest.raises(Exception):
            auth_manager.verify_token("invalid.token.here")

    def test_verify_token_tampered(self):
        token = auth_manager.issue_token()
        # Tamper with the token
        parts = token.split(".")
        tampered = parts[0] + "." + parts[1] + ".TAMPERED"
        with pytest.raises(Exception):
            auth_manager.verify_token(tampered)

    def test_verify_token_expired(self):
        # Create a token with expiry in the past by temporarily overriding
        original_expiry = auth_manager.jwt_expiry_seconds
        try:
            auth_manager.jwt_expiry_seconds = -3600  # Expired 1 hour ago
            token = auth_manager.issue_token()
            with pytest.raises(Exception):
                auth_manager.verify_token(token)
        finally:
            auth_manager.jwt_expiry_seconds = original_expiry


class TestAuthEndpoints:
    """Tests for auth-related API endpoints."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from api.app import app
        return TestClient(app)

    def test_token_endpoint_requires_api_key(self, client):
        resp = client.post("/auth/token")
        assert resp.status_code in (401, 422)

    def test_token_endpoint_wrong_key(self, client):
        resp = client.post(
            "/auth/token?api_key=wrong",
            headers={"X-API-Key": "wrong"}
        )
        assert resp.status_code == 401

    def test_token_endpoint_valid(self, client):
        resp = client.post(
            f"/auth/token?api_key={auth_manager.api_key}",
            headers={"X-API-Key": auth_manager.api_key}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    def test_search_with_jwt(self, client):
        # Get token
        token_resp = client.post(
            f"/auth/token?api_key={auth_manager.api_key}",
            headers={"X-API-Key": auth_manager.api_key}
        )
        token = token_resp.json()["access_token"]

        # Use token for search
        resp = client.post(
            "/search",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": "test", "page": 1, "page_size": 1}
        )
        assert resp.status_code == 200

    def test_search_with_invalid_jwt(self, client):
        resp = client.post(
            "/search",
            headers={"Authorization": "Bearer invalid.jwt.token"},
            json={"query": "test", "page": 1, "page_size": 1}
        )
        assert resp.status_code in (400, 401)


class TestSecurityHeaders:
    """Tests for security-related response headers."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from api.app import app
        return TestClient(app)

    def test_cors_headers(self, client):
        resp = client.options(
            "/search",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
            }
        )
        # CORS should allow the frontend origin
        assert resp.status_code in (200, 405)

    def test_rate_limit_headers(self, client):
        resp = client.get(
            "/status",
            headers={"X-API-Key": auth_manager.api_key}
        )
        assert "X-RateLimit-Limit" in resp.headers
        assert "X-RateLimit-Remaining" in resp.headers
        assert "X-RateLimit-Reset" in resp.headers
