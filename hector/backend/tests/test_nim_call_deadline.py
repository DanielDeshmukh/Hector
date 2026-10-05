"""
Tests for the NIM wall-clock call deadline (api/core/nim_llm.py).

The client's timeout=120 is an httpx *read* timeout and cannot stop a call
that keeps the socket open; in eval iter4 three such calls ran ~2h each and
stalled every evaluation worker. call_with_deadline() enforces a true
wall-clock ceiling instead.
"""

import os
import sys
import threading
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.nim_llm import CALL_DEADLINE_S, call_with_deadline


class TestCallWithDeadline:
    def test_fast_call_returns_value(self):
        assert call_with_deadline(lambda x: x * 2, 5, x=21) == 42

    def test_hung_call_raises_timeout(self):
        def hang():
            time.sleep(30)

        t0 = time.time()
        with pytest.raises(TimeoutError):
            call_with_deadline(hang, 0.4)
        elapsed = time.time() - t0
        assert elapsed < 3.0, f"deadline not enforced, waited {elapsed:.1f}s"

    def test_hung_call_releases_caller_fast(self):
        """A stuck call must not occupy its caller (pool worker) past the deadline."""
        release = threading.Event()

        def hang():
            release.wait(30)

        with pytest.raises(TimeoutError):
            call_with_deadline(hang, 0.3)
        release.set()

    def test_zero_disables_deadline(self):
        assert call_with_deadline(lambda: "ok", 0) == "ok"

    def test_inner_exception_propagates_unchanged(self):
        def boom():
            raise ValueError("bad request")

        with pytest.raises(ValueError, match="bad request"):
            call_with_deadline(boom, 5)

    def test_slow_but_within_deadline_succeeds(self):
        def slow():
            time.sleep(0.6)
            return "late"

        assert call_with_deadline(slow, 5) == "late"

    def test_abandoned_thread_does_not_block_interpreter_exit(self):
        """Daemon flag: an abandoned call must never be joined at shutdown."""
        def hang():
            time.sleep(30)

        with pytest.raises(TimeoutError):
            call_with_deadline(hang, 0.2)
        thread = next(
            (t for t in threading.enumerate() if t.name == "nim-call-deadline"),
            None,
        )
        assert thread is None or thread.daemon


class TestDeadlineConfig:
    def test_default_deadline_is_positive(self):
        assert CALL_DEADLINE_S > 0, "a ceiling must be on by default"

    def test_retry_treats_timeout_as_transient(self):
        """A deadline breach must be retried, not raised to the caller."""
        from utils.retry import retry

        calls = {"n": 0}

        def flaky():
            calls["n"] += 1
            if calls["n"] == 1:
                raise TimeoutError("NIM call exceeded 300s wall-clock deadline")
            return "recovered"

        assert retry(flaky, max_attempts=3, base_delay=0.01) == "recovered"
        assert calls["n"] == 2
