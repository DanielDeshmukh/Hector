"""Tests for log redaction filter."""

import logging
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.log_redaction import RedactionFilter, install_redaction_filter


class TestRedactionFilter:
    """Tests for the RedactionFilter class."""

    @pytest.fixture
    def logger(self):
        logger = logging.getLogger("test_redaction")
        logger.handlers.clear()
        handler = logging.StreamHandler(open(os.devnull, "w"))
        handler.addFilter(RedactionFilter("test"))
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        yield logger
        logger.handlers.clear()

    def test_api_key_redacted(self, logger):
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="api_key=sk-test12345678901234567890",
            args=(),
            exc_info=None,
        )
        f = RedactionFilter("test")
        f.filter(record)
        assert "sk-test12345678901234567890" not in record.msg
        assert "[REDACTED]" in record.msg

    def test_x_api_key_header_redacted(self, logger):
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="X-API-Key: my-secret-api-key-12345678901234",
            args=(),
            exc_info=None,
        )
        f = RedactionFilter("test")
        f.filter(record)
        assert "my-secret-api-key-12345678901234" not in record.msg
        assert "[REDACTED]" in record.msg

    def test_bearer_token_redacted(self, logger):
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.test.signature",
            args=(),
            exc_info=None,
        )
        f = RedactionFilter("test")
        f.filter(record)
        assert "eyJhbGciOiJIUzI1NiJ9" not in record.msg
        assert "[REDACTED_JWT]" in record.msg

    def test_password_redacted(self, logger):
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="password=supersecret123",
            args=(),
            exc_info=None,
        )
        f = RedactionFilter("test")
        f.filter(record)
        assert "supersecret123" not in record.msg
        assert "[REDACTED]" in record.msg

    def test_jwt_secret_redacted(self, logger):
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="jwt_secret=my-super-secret-jwt-key-32bytes!!",
            args=(),
            exc_info=None,
        )
        f = RedactionFilter("test")
        f.filter(record)
        assert "my-super-secret-jwt-key-32bytes!!" not in record.msg
        assert "[REDACTED]" in record.msg

    def test_groq_api_key_redacted(self, logger):
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Using gsk_abc123def456ghi789jkl012mno345pqr678stu901vwx234",
            args=(),
            exc_info=None,
        )
        f = RedactionFilter("test")
        f.filter(record)
        assert "gsk_abc123def456" not in record.msg
        assert "[REDACTED]" in record.msg

    def test_postgres_password_redacted(self, logger):
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="POSTGRES_PASSWORD=mydbpass123",
            args=(),
            exc_info=None,
        )
        f = RedactionFilter("test")
        f.filter(record)
        assert "mydbpass123" not in record.msg
        assert "[REDACTED]" in record.msg

    def test_postgres_connection_string_redacted(self, logger):
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="postgresql://hector:mypassword@postgres:5432/hector",
            args=(),
            exc_info=None,
        )
        f = RedactionFilter("test")
        f.filter(record)
        assert "mypassword" not in record.msg
        assert "[REDACTED]" in record.msg

    def test_clean_message_unchanged(self, logger):
        msg = "search route=LEGAL_RESEARCH results=5 duration=12.3ms"
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg=msg,
            args=(),
            exc_info=None,
        )
        f = RedactionFilter("test")
        f.filter(record)
        assert record.msg == msg

    def test_tuple_args_redacted(self):
        f = RedactionFilter("test")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="auth event=login subject=%s success=%s",
            args=("user@test.com", "api_key=secret-key-1234567890"),
            exc_info=None,
        )
        f.filter(record)
        assert "secret-key-1234567890" not in str(record.args)
        assert "[REDACTED]" in str(record.args)

    def test_dict_args_redacted(self):
        f = RedactionFilter("test")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="request headers=%s",
            args=({"X-API-Key": "my-secret-api-key-1234567890"},),
            exc_info=None,
        )
        f.filter(record)
        assert "my-secret-api-key-1234567890" not in str(record.args)


class TestInstallRedactionFilter:
    """Tests for install_redaction_filter function."""

    def test_filter_installed(self):
        install_redaction_filter()
        root_logger = logging.getLogger()
        filter_names = [f.name for f in root_logger.filters]
        assert "hector_redaction" in filter_names

    def test_filter_returns_true(self):
        f = RedactionFilter("test")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test message",
            args=(),
            exc_info=None,
        )
        assert f.filter(record) is True
