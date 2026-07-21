"""
Input Validation and Sanitization for HECTOR Enterprise.
Provides strict input validation and data sanitization.
"""

from __future__ import annotations
import re
import html
import hashlib
import secrets


class ValidationError(Exception):
    """Raised when input validation fails."""

    pass


class InputSanitizer:
    """Sanitizes user input to prevent injection attacks."""

    @staticmethod
    def sanitize_string(value: str, max_length: int = 10000) -> str:
        """Sanitize a string input."""
        if not isinstance(value, str):
            raise ValidationError("Input must be a string")

        # Trim to max length
        value = value[:max_length]

        # Remove null bytes
        value = value.replace("\x00", "")

        # Strip dangerous protocol prefixes
        dangerous_protocols = ["javascript:", "vbscript:", "data:"]
        value_lower = value.lower()
        for protocol in dangerous_protocols:
            if value_lower.startswith(protocol):
                value = value[len(protocol) :]
                value_lower = value.lower()

        # HTML escape to prevent XSS
        value = html.escape(value)

        return value.strip()

    @staticmethod
    def sanitize_search_query(query: str) -> str:
        """Sanitize search queries - more restrictive."""
        if not query or not isinstance(query, str):
            raise ValidationError("Search query is required")

        # Trim length
        query = query[:1000].strip()

        if len(query) < 1:
            raise ValidationError("Search query is too short")

        # Remove potentially dangerous characters
        # Allow: letters, numbers, spaces, basic punctuation (no semicolons/colons for SQL safety)
        allowed_pattern = re.compile(r"^[a-zA-Z0-9\s\-.,()'\"!?]+$")
        if not allowed_pattern.match(query):
            raise ValidationError("Search query contains invalid characters")

        # Normalize whitespace
        query = re.sub(r"\s+", " ", query)

        return query

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize a filename."""
        if not filename or not isinstance(filename, str):
            raise ValidationError("Filename is required")

        # Remove path separators
        filename = filename.replace("/", "").replace("\\", "")

        # Remove directory traversal sequences
        filename = filename.replace("..", "")

        # Remove dangerous extensions
        dangerous_exts = [".exe", ".bat", ".cmd", ".sh", ".ps1", ".js", ".vbs"]
        for ext in dangerous_exts:
            if filename.lower().endswith(ext):
                raise ValidationError(f"Extension {ext} is not allowed")

        # Allow only safe characters
        safe_pattern = re.compile(r"^[a-zA-Z0-9._\-]+$")
        if not safe_pattern.match(filename):
            raise ValidationError("Filename contains invalid characters")

        return filename[:255]

    @staticmethod
    def sanitize_email(email: str) -> str:
        """Sanitize and validate email address."""
        if not email or not isinstance(email, str):
            raise ValidationError("Email is required")

        email = email.strip().lower()[:254]

        # Basic email pattern
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, email):
            raise ValidationError("Invalid email format")

        return email

    @staticmethod
    def sanitize_username(username: str) -> str:
        """Sanitize username."""
        if not username or not isinstance(username, str):
            raise ValidationError("Username is required")

        username = username.strip()[:50]

        # Alphanumeric and underscore only
        pattern = re.compile(r"^[a-zA-Z0-9_]+$")
        if not pattern.match(username):
            raise ValidationError(
                "Username can only contain letters, numbers, and underscores"
            )

        return username

    @staticmethod
    def sanitize_api_key(api_key: str) -> str:
        """Sanitize API key - validate format."""
        if not api_key or not isinstance(api_key, str):
            raise ValidationError("API key is required")

        # Validate format (hex or base64, 32-256 chars)
        if len(api_key) < 32 or len(api_key) > 256:
            raise ValidationError("API key must be 32-256 characters")

        # Allow hex or base64 characters
        pattern = re.compile(r"^[a-zA-Z0-9+/=_-]+$")
        if not pattern.match(api_key):
            raise ValidationError("API key contains invalid characters")

        return api_key


class InputValidator:
    """Validates various input types with strict rules."""

    @staticmethod
    def validate_search_request(query: str, top_k: int | None = None) -> dict:
        """Validate a search request."""
        errors = []

        # Validate query
        try:
            sanitized_query = InputSanitizer.sanitize_search_query(query)
        except ValidationError as e:
            errors.append(f"Query: {str(e)}")

        # Validate top_k if provided
        sanitized_top_k = 10  # default
        if top_k is not None:
            if not isinstance(top_k, int):
                errors.append("top_k must be an integer")
            elif top_k < 1 or top_k > 100:
                errors.append("top_k must be between 1 and 100")
            else:
                sanitized_top_k = top_k

        if errors:
            raise ValidationError("; ".join(errors))

        return {"query": sanitized_query, "top_k": sanitized_top_k}

    @staticmethod
    def validate_user_registration(username: str, email: str, password: str) -> dict:
        """Validate user registration data."""
        errors = []

        # Validate username
        try:
            sanitized_username = InputSanitizer.sanitize_username(username)
        except ValidationError as e:
            errors.append(str(e))

        # Validate email
        try:
            sanitized_email = InputSanitizer.sanitize_email(email)
        except ValidationError as e:
            errors.append(str(e))

        # Validate password strength
        if not password or len(password) < 8:
            errors.append("Password must be at least 8 characters")
        if len(password) > 128:
            errors.append("Password is too long")

        # Check password complexity
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        if not (has_upper and has_lower and has_digit):
            errors.append("Password must contain uppercase, lowercase, and digit")

        if errors:
            raise ValidationError("; ".join(errors))

        return {
            "username": sanitized_username,
            "email": sanitized_email,
            "password_hash": hashlib.sha256(password.encode()).hexdigest(),
        }

    @staticmethod
    def validate_file_upload(filename: str, content_type: str, file_size: int) -> dict:
        """Validate file upload data."""
        errors = []

        # Validate filename
        try:
            safe_filename = InputSanitizer.sanitize_filename(filename)
        except ValidationError as e:
            errors.append(str(e))

        # Validate content type
        allowed_types = [
            "application/pdf",
            "text/plain",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ]
        if content_type not in allowed_types:
            errors.append(f"File type {content_type} is not allowed")

        # Validate file size (max 50MB)
        max_size = 50 * 1024 * 1024  # 50MB
        if file_size > max_size:
            errors.append(f"File size exceeds maximum of {max_size // (1024 * 1024)}MB")
        if file_size < 1:
            errors.append("File is empty")

        if errors:
            raise ValidationError("; ".join(errors))

        return {
            "filename": safe_filename,
            "content_type": content_type,
            "size": file_size,
        }


class RateLimitValidator:
    """Validates rate limiting parameters."""

    @staticmethod
    def validate_rate_limit_config(
        requests_per_minute: int, burst_size: int | None = None
    ) -> dict:
        """Validate rate limit configuration."""
        errors = []

        if not isinstance(requests_per_minute, int):
            errors.append("requests_per_minute must be an integer")
        elif requests_per_minute < 1:
            errors.append("requests_per_minute must be at least 1")
        elif requests_per_minute > 1000:
            errors.append("requests_per_minute cannot exceed 1000")

        if burst_size is not None:
            if not isinstance(burst_size, int):
                errors.append("burst_size must be an integer")
            elif burst_size < 1:
                errors.append("burst_size must be at least 1")
            elif burst_size > requests_per_minute * 2:
                errors.append("burst_size is too large relative to requests_per_minute")

        if errors:
            raise ValidationError("; ".join(errors))

        return {
            "requests_per_minute": requests_per_minute,
            "burst_size": burst_size or requests_per_minute,
        }


def validate_json_payload(payload: dict, required_fields: list[str]) -> dict:
    """Validate JSON payload has required fields."""
    missing = [f for f in required_fields if f not in payload]
    if missing:
        raise ValidationError(f"Missing required fields: {', '.join(missing)}")

    # Return sanitized payload
    return {k: str(v)[:10000] for k, v in payload.items()}


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure token."""
    return secrets.token_urlsafe(length)


def hash_sensitive_data(data: str, salt: str = "") -> str:
    """Hash sensitive data with salt."""
    return hashlib.pbkdf2_hmac(
        "sha256", data.encode("utf-8"), salt.encode("utf-8"), 100000
    ).hex()


class DataSanitizer:
    """Sanitizes output data for safe display."""

    @staticmethod
    def sanitize_user_output(user_data: dict) -> dict:
        """Remove sensitive fields from user data for output."""
        # Create copy
        safe = user_data.copy()

        # Remove sensitive fields
        sensitive_fields = ["password_hash", "api_key", "secret", "token"]
        for field in sensitive_fields:
            if field in safe:
                safe[field] = "***REDACTED***"

        # Mask email
        if "email" in safe:
            email = safe["email"]
            if "@" in email:
                parts = email.split("@")
                safe["email"] = parts[0][:2] + "***@" + parts[1]

        return safe

    @staticmethod
    def sanitize_error_message(error: Exception) -> str:
        """Sanitize error messages for client display."""
        msg = str(error)

        # Don't expose internal paths
        msg = re.sub(r"[A-Za-z]:\\[^\s]+", "[PATH]", msg)
        msg = re.sub(r"/[^\s]+/hector/", "/hector/", msg)

        # Generic messages for internal errors
        internal_patterns = ["Traceback", 'File "', "line ", "ModuleNotFound"]
        for pattern in internal_patterns:
            if pattern in msg:
                return "An internal error occurred. Please contact support."

        return msg[:500]
