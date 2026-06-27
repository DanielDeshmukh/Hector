"""Log redaction filter to scrub sensitive data from log records."""

import re
import logging
from typing import Any


# Patterns for sensitive data
_PATTERNS = [
    # API keys (various formats)
    (re.compile(r"(api[_-]?key[=:]\s*)([\w\-]{20,})", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(X-API-Key[:\s]+)([\w\-]{20,})", re.IGNORECASE), r"\1[REDACTED]"),
    # JWT tokens
    (re.compile(r"(Bearer\s+)([\w\-]+\.[\w\-]+\.[\w\-]+)", re.IGNORECASE), r"\1[REDACTED_JWT]"),
    (re.compile(r"(access[_-]?token[=:]\s*)([\w\-]+\.[\w\-]+\.[\w\-]+)", re.IGNORECASE), r"\1[REDACTED_JWT]"),
    # Passwords
    (re.compile(r"(password[=:]\s*)(\S+)", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(POSTGRES_PASSWORD[=:]\s*)(\S+)", re.IGNORECASE), r"\1[REDACTED]"),
    # Secrets
    (re.compile(r"(jwt[_-]?secret[=:]\s*)(\S+)", re.IGNORECASE), r"\1[REDACTED]"),
    (re.compile(r"(secret[_-]?key[=:]\s*)(\S+)", re.IGNORECASE), r"\1[REDACTED]"),
    # Groq/LLM API keys
    (re.compile(r"(gsk_[\w]{20,})", re.IGNORECASE), lambda m: m.group(0)[:8] + "[REDACTED]"),
    # Database connection strings
    (re.compile(r"(postgresql://\w+:\w+@)", re.IGNORECASE), r"postgresql://[REDACTED]:[REDACTED]@"),
    (re.compile(r"(redis://:\w+@)", re.IGNORECASE), r"redis://:[REDACTED]@"),
]

# Patterns applied to dict values (standalone secrets without key= prefix)
_DICT_VALUE_PATTERNS = [
    (re.compile(r"^(gsk_[\w]{20,})$", re.IGNORECASE), lambda m: m.group(0)[:8] + "[REDACTED]"),
    (re.compile(r"^([\w\-]{30,})$"), "[REDACTED]"),
]


class RedactionFilter(logging.Filter):
    """Logging filter that redacts sensitive data from log records."""

    def __init__(self, name: str = ""):
        super().__init__(name)

    def filter(self, record: logging.LogRecord) -> bool:
        # Redact the log message
        if record.msg and isinstance(record.msg, str):
            for pattern, replacement in _PATTERNS:
                record.msg = pattern.sub(replacement, record.msg)

        # Redact any args that might contain secrets
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: self._redact_dict_value(k, v) for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                redacted = []
                for a in record.args:
                    if isinstance(a, dict):
                        redacted.append({k: self._redact_dict_value(k, v) for k, v in a.items()})
                    else:
                        redacted.append(self._redact_value(a))
                record.args = tuple(redacted)

        return True

    def _redact_value(self, value: Any) -> Any:
        """Redact a single value if it looks like a secret."""
        if isinstance(value, str):
            for pattern, replacement in _PATTERNS:
                value = pattern.sub(replacement, value)
        elif isinstance(value, dict):
            value = {k: self._redact_dict_value(k, v) for k, v in value.items()}
        elif isinstance(value, (list, tuple)):
            value = type(value)(self._redact_value(v) for v in value)
        return value

    def _redact_dict_value(self, key: str, value: Any) -> Any:
        """Redact a dict value. Keys suggesting secrets trigger redaction."""
        SECRET_KEYS = {"api_key", "apikey", "password", "secret", "jwt_secret",
                       "secret_key", "access_token", "authorization", "token",
                       "jwtsecret", "jwt_secret", "x_api_key"}
        normalized = key.lower().replace("-", "_").replace(" ", "_")
        if normalized in SECRET_KEYS:
            if isinstance(value, str) and len(value) > 8:
                return value[:4] + "[REDACTED]"
            return "[REDACTED]"
        if isinstance(value, str):
            for pattern, replacement in _PATTERNS:
                value = pattern.sub(replacement, value)
        return value


def install_redaction_filter():
    """Install the redaction filter on the root logger."""
    redaction_filter = RedactionFilter("hector_redaction")
    logging.getLogger().addFilter(redaction_filter)
