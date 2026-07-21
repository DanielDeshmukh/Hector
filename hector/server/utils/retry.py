"""
Retry utility with exponential backoff for transient failures.
"""

import logging
import os
import time
from typing import Any, Callable

logger = logging.getLogger(__name__)

# Configurable via env vars
_MAX_ATTEMPTS = int(os.getenv("HECTOR_RETRY_MAX_ATTEMPTS", "3"))
_BASE_DELAY = float(os.getenv("HECTOR_RETRY_BASE_DELAY", "0.5"))
_MAX_DELAY = float(os.getenv("HECTOR_RETRY_MAX_DELAY", "10.0"))
_BACKOFF_FACTOR = float(os.getenv("HECTOR_RETRY_BACKOFF_FACTOR", "2.0"))


def retry(
    func: Callable,
    *args,
    max_attempts: int | None = None,
    base_delay: float | None = None,
    max_delay: float | None = None,
    backoff_factor: float | None = None,
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
    operation_name: str = "operation",
    **kwargs,
) -> Any:
    """
    Execute a function with retry and exponential backoff.

    Args:
        func: Function to call.
        *args: Positional arguments for func.
        max_attempts: Maximum number of attempts (default: HECTOR_RETRY_MAX_ATTEMPTS or 3).
        base_delay: Initial delay in seconds (default: HECTOR_RETRY_BASE_DELAY or 0.5).
        max_delay: Maximum delay in seconds (default: HECTOR_RETRY_MAX_DELAY or 10.0).
        backoff_factor: Multiplier for each retry (default: HECTOR_RETRY_BACKOFF_FACTOR or 2.0).
        retryable_exceptions: Tuple of exception types to retry on (default: all Exception).
        operation_name: Human-readable name for logging.
        **kwargs: Keyword arguments for func.

    Returns:
        Result of func(*args, **kwargs).

    Raises:
        The last exception if all attempts fail.
    """
    _max = max_attempts if max_attempts is not None else _MAX_ATTEMPTS
    _base = base_delay if base_delay is not None else _BASE_DELAY
    _max_d = max_delay if max_delay is not None else _MAX_DELAY
    _factor = backoff_factor if backoff_factor is not None else _BACKOFF_FACTOR

    last_exc = None
    for attempt in range(1, _max + 1):
        try:
            return func(*args, **kwargs)
        except retryable_exceptions as exc:
            last_exc = exc
            if attempt == _max:
                logger.error(
                    "%s failed after %d attempts: %s",
                    operation_name,
                    _max,
                    exc,
                )
                raise

            delay = min(_base * (_factor ** (attempt - 1)), _max_d)
            logger.warning(
                "%s failed (attempt %d/%d): %s — retrying in %.1fs",
                operation_name,
                attempt,
                _max,
                exc,
                delay,
            )
            time.sleep(delay)

    raise last_exc  # unreachable but satisfies type checker
