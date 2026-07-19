"""
Unit tests for Input Validators and Sanitizers.
Tests data validation and sanitization functions.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.enterprise.validators import (
    InputSanitizer,
    InputValidator,
    ValidationError,
    generate_secure_token,
    hash_sensitive_data,
    DataSanitizer,
)


class TestInputSanitizer:
    """Test input sanitization."""

    def test_sanitize_string_basic(self):
        """Test basic string sanitization."""
        result = InputSanitizer.sanitize_string("Hello World")
        assert result == "Hello World"

    def test_sanitize_string_xss_prevention(self):
        """Test XSS prevention in sanitization."""
        result = InputSanitizer.sanitize_string("<script>alert('xss')</script>")
        assert "<script>" not in result
        assert "&lt;script" in result

    def test_sanitize_string_max_length(self):
        """Test string length limitation."""
        long_string = "x" * 20000
        result = InputSanitizer.sanitize_string(long_string)
        assert len(result) <= 10000

    def test_sanitize_string_null_bytes(self):
        """Test null byte removal."""
        result = InputSanitizer.sanitize_string("test\x00value")
        assert "\x00" not in result

    def test_sanitize_search_query_valid(self):
        """Test valid search query."""
        result = InputSanitizer.sanitize_search_query("murder section 302 BNS")
        assert result == "murder section 302 BNS"

    def test_sanitize_search_query_too_short(self):
        """Test search query too short."""
        with pytest.raises(ValidationError):
            InputSanitizer.sanitize_search_query("")

    def test_sanitize_search_query_invalid_chars(self):
        """Test search query with invalid characters."""
        with pytest.raises(ValidationError):
            InputSanitizer.sanitize_search_query("test; DROP TABLE")

    def test_sanitize_filename_valid(self):
        """Test valid filename."""
        result = InputSanitizer.sanitize_filename("document.pdf")
        assert result == "document.pdf"

    def test_sanitize_filename_dangerous_ext(self):
        """Test dangerous file extension rejection."""
        with pytest.raises(ValidationError):
            InputSanitizer.sanitize_filename("malware.exe")

    def test_sanitize_filename_path_separators(self):
        """Test path separator removal."""
        result = InputSanitizer.sanitize_filename("../etc/passwd")
        assert ".." not in result

    def test_sanitize_email_valid(self):
        """Test valid email."""
        result = InputSanitizer.sanitize_email("user@example.com")
        assert result == "user@example.com"

    def test_sanitize_email_invalid(self):
        """Test invalid email rejection."""
        with pytest.raises(ValidationError):
            InputSanitizer.sanitize_email("invalid-email")

    def test_sanitize_username_valid(self):
        """Test valid username."""
        result = InputSanitizer.sanitize_username("user_123")
        assert result == "user_123"

    def test_sanitize_username_invalid_chars(self):
        """Test invalid username characters."""
        with pytest.raises(ValidationError):
            InputSanitizer.sanitize_username("user@admin")

    def test_sanitize_api_key_valid(self):
        """Test valid API key."""
        key = "a" * 40
        result = InputSanitizer.sanitize_api_key(key)
        assert result == key

    def test_sanitize_api_key_too_short(self):
        """Test API key too short."""
        with pytest.raises(ValidationError):
            InputSanitizer.sanitize_api_key("short")


class TestInputValidator:
    """Test input validation."""

    def test_validate_search_request_valid(self):
        """Test valid search request."""
        result = InputValidator.validate_search_request("test query", top_k=10)
        assert result["query"] == "test query"
        assert result["top_k"] == 10

    def test_validate_search_request_default_top_k(self):
        """Test default top_k value."""
        result = InputValidator.validate_search_request("test")
        assert result["top_k"] == 10

    def test_validate_search_request_invalid_top_k(self):
        """Test invalid top_k rejection."""
        with pytest.raises(ValidationError):
            InputValidator.validate_search_request("test", top_k=0)

    def test_validate_search_request_top_k_too_large(self):
        """Test top_k too large rejection."""
        with pytest.raises(ValidationError):
            InputValidator.validate_search_request("test", top_k=200)

    def test_validate_user_registration_valid(self):
        """Test valid user registration."""
        result = InputValidator.validate_user_registration(
            "testuser", "test@example.com", "Password123"
        )
        assert result["username"] == "testuser"
        assert result["email"] == "test@example.com"
        assert "password_hash" in result

    def test_validate_user_registration_password_too_short(self):
        """Test password too short rejection."""
        with pytest.raises(ValidationError):
            InputValidator.validate_user_registration(
                "user", "test@example.com", "short"
            )

    def test_validate_user_registration_password_no_complexity(self):
        """Test password complexity requirement."""
        with pytest.raises(ValidationError):
            InputValidator.validate_user_registration(
                "user", "test@example.com", "alllowercase"
            )

    def test_validate_file_upload_valid(self):
        """Test valid file upload."""
        result = InputValidator.validate_file_upload(
            "document.pdf", "application/pdf", 1024
        )
        assert result["filename"] == "document.pdf"
        assert result["size"] == 1024

    def test_validate_file_upload_invalid_type(self):
        """Test invalid file type rejection."""
        with pytest.raises(ValidationError):
            InputValidator.validate_file_upload("malware.exe", "application/exe", 1024)

    def test_validate_file_upload_too_large(self):
        """Test file too large rejection."""
        with pytest.raises(ValidationError):
            InputValidator.validate_file_upload(
                "large.pdf", "application/pdf", 100 * 1024 * 1024
            )


class TestDataSanitizer:
    """Test data sanitization for output."""

    def test_sanitize_user_output(self):
        """Test user data sanitization."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password_hash": "secret",
            "api_key": "key123",
        }
        result = DataSanitizer.sanitize_user_output(user_data)
        assert result["password_hash"] == "***REDACTED***"
        assert result["api_key"] == "***REDACTED***"

    def test_sanitize_error_message_internal(self):
        """Test internal error message sanitization."""
        error = Exception("Traceback (most recent call last):\n  File test.py")
        result = DataSanitizer.sanitize_error_message(error)
        assert "Traceback" not in result


class TestUtilityFunctions:
    """Test utility functions."""

    def test_generate_secure_token(self):
        """Test secure token generation."""
        token1 = generate_secure_token()
        token2 = generate_secure_token()
        assert len(token1) >= 32
        assert token1 != token2

    def test_hash_sensitive_data(self):
        """Test sensitive data hashing."""
        hash1 = hash_sensitive_data("password", "salt")
        hash2 = hash_sensitive_data("password", "salt")
        hash3 = hash_sensitive_data("different", "salt")
        assert hash1 == hash2
        assert hash1 != hash3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
