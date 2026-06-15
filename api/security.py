import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any

from fastapi import Header, HTTPException, status


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(raw: str) -> bytes:
    padding = "=" * (-len(raw) % 4)
    return base64.urlsafe_b64decode(raw + padding)


class AuthManager:
    _WEAK_SECRETS = {"hector-dev-secret", "change-me-in-production", "secret", "jwt-secret"}

    def __init__(self):
        self.api_key = os.getenv("HECTOR_API_KEY", "")
        self.jwt_secret = os.getenv("HECTOR_JWT_SECRET", "")
        self.jwt_expiry_seconds = int(os.getenv("HECTOR_JWT_EXPIRY_SECONDS", "3600"))

        if not self.jwt_secret or self.jwt_secret in self._WEAK_SECRETS:
            raise RuntimeError(
                "HECTOR_JWT_SECRET must be set to a strong random value. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        if not self.api_key:
            raise RuntimeError(
                "HECTOR_API_KEY must be set. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )

    def issue_token(self, subject: str = "hector-client") -> str:
        issued_at = int(time.time())
        payload = {
            "sub": subject,
            "iat": issued_at,
            "exp": issued_at + self.jwt_expiry_seconds,
        }
        header = {"alg": "HS256", "typ": "JWT"}

        encoded_header = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
        encoded_payload = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")
        signature = hmac.new(
            self.jwt_secret.encode("utf-8"),
            signing_input,
            hashlib.sha256,
        ).digest()
        return f"{encoded_header}.{encoded_payload}.{_b64url_encode(signature)}"

    def verify_api_key(self, candidate: str | None) -> bool:
        return bool(candidate) and hmac.compare_digest(candidate, self.api_key)

    def verify_token(self, token: str | None) -> dict[str, Any]:
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing bearer token.",
            )

        try:
            encoded_header, encoded_payload, encoded_signature = token.split(".")
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Malformed bearer token.",
            ) from exc

        signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")
        expected_signature = hmac.new(
            self.jwt_secret.encode("utf-8"),
            signing_input,
            hashlib.sha256,
        ).digest()
        actual_signature = _b64url_decode(encoded_signature)

        if not hmac.compare_digest(expected_signature, actual_signature):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid bearer token signature.",
            )

        payload = json.loads(_b64url_decode(encoded_payload).decode("utf-8"))
        if int(payload.get("exp", 0)) < int(time.time()):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Bearer token has expired.",
            )
        return payload

    def authenticate_headers(
        self,
        authorization: str | None = None,
        x_api_key: str | None = None,
    ) -> dict[str, Any]:
        if self.verify_api_key(x_api_key):
            return {"auth_type": "api_key", "subject": "api-key-client"}

        if authorization and authorization.lower().startswith("bearer "):
            payload = self.verify_token(authorization.split(" ", 1)[1].strip())
            return {"auth_type": "jwt", "subject": payload.get("sub", "jwt-client")}

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required via X-API-Key or Bearer token.",
        )


auth_manager = AuthManager()


def require_auth(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
):
    return auth_manager.authenticate_headers(authorization=authorization, x_api_key=x_api_key)
