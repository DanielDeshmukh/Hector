"""
NVIDIA NIM LLM Client.
Wraps the NIM OpenAI-compatible API for chat completions.
Used for intent routing and response generation.
"""

import json
import logging
import os
import threading
from typing import Any, Callable

from dotenv import load_dotenv

from utils.retry import retry

load_dotenv()

logger = logging.getLogger("hector.nim_llm")

NIM_BASE_URL = os.getenv("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
NIM_API_KEY = os.getenv("NIM_API_KEY") or os.getenv("NVIDIA_API_KEY")
# Every model id previously defaulted here is gone: meta/llama-3.1-8b-instruct
# was retired 2026-08-26 and nvidia/llama-3.1-nemotron-nano-8b-v1 likewise
# (both HTTP 410), so the production defaults were failing on every call.
# Verified 2026-10-03 against this account's /models + live completions:
# only nemotron-3-ultra-550b-a55b, nemotron-3-nano-omni-30b-a3b-reasoning and
# nemotron-3.5-lightning-30b-a3b answer (the rest 404 for this account).
# lightning emits a "thinking process" preamble, so it is not used here.
DEFAULT_CHAT_MODEL = os.getenv(
    "HECTOR_NIM_CHAT_MODEL", "nvidia/nemotron-3-ultra-550b-a55b"
)

# Hard wall-clock ceiling for ONE completions attempt.
#
# The OpenAI client's timeout=120 below is an httpx *read* timeout: it fires
# only after 120s with no bytes on the socket. A server that trickles bytes
# (very slow generation) or a gateway that parks the connection never trips
# it. Measured 2026-10-03 in eval iter4: three calls (ipc-197-a, ipc-171A-a,
# ipc-78-b) each ran ~7,390s (2h03m) and returned successfully, and with
# HECTOR_EVAL_WORKERS=3 all three pool workers were occupied, so the whole
# evaluation stalled behind them. A wall-clock deadline is independent of
# byte arrival; exceeding it raises TimeoutError, which retry() treats as
# transient and retries. 0 disables the deadline.
CALL_DEADLINE_S = float(os.getenv("HECTOR_NIM_CALL_DEADLINE_S", "300") or 0)


def call_with_deadline(
    func: Callable[..., Any], deadline_s: float, **kwargs: Any
) -> Any:
    """Run func(**kwargs), abandoning it after deadline_s of wall-clock time.

    The call runs in a *daemon* thread: the caller stops waiting at the
    deadline and the abandoned call can never block interpreter shutdown
    (a ThreadPoolExecutor worker thread is non-daemon and would be joined
    at exit, reintroducing the stall at process end).
    """
    if deadline_s <= 0:
        return func(**kwargs)
    box: dict[str, Any] = {}

    def runner() -> None:
        try:
            box["value"] = func(**kwargs)
        except BaseException as exc:  # re-raised in the caller's thread
            box["error"] = exc

    worker = threading.Thread(
        target=runner, daemon=True, name="nim-call-deadline"
    )
    worker.start()
    worker.join(deadline_s)
    if "value" in box:
        return box["value"]
    if "error" in box:
        raise box["error"]
    raise TimeoutError(
        f"NIM call exceeded {deadline_s:.0f}s wall-clock deadline"
    )

# Model registry — different models for different pipeline stages.
# Each env value may be a comma-separated fallback chain (tried in order).
NIM_MODELS = {
    "router": os.getenv(
        "HECTOR_NIM_ROUTER_MODEL", "nvidia/nemotron-3-ultra-550b-a55b"
    ),
    "generation": os.getenv(
        "HECTOR_NIM_GENERATION_MODEL", "nvidia/nemotron-3-ultra-550b-a55b"
    ),
    "verification": os.getenv(
        "HECTOR_NIM_VERIFICATION_MODEL", "nvidia/nemotron-3-ultra-550b-a55b"
    ),
    "query_intelligence": os.getenv(
        "HECTOR_NIM_QI_MODEL",
        "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
    ),
    # Compare synthesis: small/fast JSON formatting only (chunk-grounded).
    # 2026-10-06 measurements on this account: nano-omni answers JSON mode
    # in ~2.9s when admitted, but its worker pool is often at 16/16
    # (503 ResourceExhausted -> in-call retries, ~10s end-to-end); ultra
    # has its own congestion (one measured >20s hang on an idle prompt).
    # compare_synthesis walks this comma-separated chain candidate by
    # candidate with its own deadline, so both pools are usable.
    # lightning ignores JSON mode (thinking preamble), nano-3 404s.
    # Override: HECTOR_COMPARE_MODEL (comma-separated).
    "compare": os.getenv(
        "HECTOR_COMPARE_MODEL",
        "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning,"
        "nvidia/nemotron-3-ultra-550b-a55b",
    ),
}


def _split_models(value: str | None) -> list[str]:
    return [m.strip() for m in (value or "").split(",") if m.strip()]


def _is_model_dead_error(exc: Exception) -> bool:
    """True when the error means the model id itself is gone (404/410/EOL)."""
    status = getattr(exc, "status_code", None)
    if status is None:
        response = getattr(exc, "response", None)
        status = getattr(response, "status_code", None)
    if status in (404, 410):
        return True
    message = str(exc).lower()
    return any(
        marker in message
        for marker in (
            "model_not_found",
            "does not exist",
            "end of life",
            "no such model",
            "invalid model",
        )
    )


class NimLLMClient:
    """Thin wrapper around NIM's OpenAI-compatible chat completions endpoint."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ):
        self.api_key = api_key or NIM_API_KEY
        self.base_url = base_url or NIM_BASE_URL
        self.model = model or DEFAULT_CHAT_MODEL
        self._client = None

    def _get_client(self):
        if self._client is None:
            if not self.api_key:
                raise RuntimeError("NIM_API_KEY or NVIDIA_API_KEY must be set")
            try:
                from openai import OpenAI
            except ImportError:
                raise RuntimeError("openai package required: pip install openai")
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=120.0,
            )
        return self._client

    def _candidate_models(self, model: str | None) -> list[str]:
        primary = _split_models(model) or _split_models(self.model)
        fallback = _split_models(os.getenv("HECTOR_NIM_CHAT_MODEL", ""))
        return list(dict.fromkeys(primary + fallback))

    def chat(
        self,
        messages: list[dict],
        temperature: float = 0.0,
        max_tokens: int = 1024,
        response_format: dict | None = None,
        model: str | None = None,
        max_attempts: int | None = None,
    ) -> str:
        """
        Send a chat completion request to NIM.

        Args:
            messages: List of {"role": ..., "content": ...} dicts.
            temperature: Sampling temperature (0 = deterministic).
            max_tokens: Maximum tokens in response.
            response_format: Optional JSON mode dict, e.g. {"type": "json_object"}.
            model: Override model for this call. May be a comma-separated
                fallback chain of model ids, tried in order.
            max_attempts: Outer retry count (default 3). Callers that
                abandon via their own deadline must pass 1 — otherwise the
                abandoned thread keeps firing NEW requests for minutes
                (retry chains), piling load onto an already congested NIM.

        Returns:
            The assistant message content string.

        Raises:
            RuntimeError: If every configured model is unavailable/dead.
        """
        client = self._get_client()
        candidates = self._candidate_models(model)
        if not candidates:
            raise RuntimeError(
                "No NIM model configured — set HECTOR_NIM_GENERATION_MODEL or "
                "HECTOR_NIM_CHAT_MODEL (comma-separated model ids)."
            )

        last_error: Exception | None = None
        for position, candidate in enumerate(candidates):
            kwargs = {
                "model": candidate,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if response_format:
                kwargs["response_format"] = response_format

            try:
                # Bound each attempt by CALL_DEADLINE_S (see above) — the
                # client-level read timeout alone cannot stop a call that
                # keeps the socket open. TimeoutError is retryable, so a
                # stalled call costs at most deadline x attempts, not hours.
                response = retry(
                    lambda **req: call_with_deadline(
                        client.chat.completions.create, CALL_DEADLINE_S, **req
                    ),
                    max_attempts=max_attempts,
                    operation_name=f"nim_chat[{candidate}]",
                    **kwargs
                )
                return response.choices[0].message.content
            except Exception as exc:
                last_error = exc
                if not _is_model_dead_error(exc):
                    raise
                if position < len(candidates) - 1:
                    logger.warning(
                        "NIM model %r unavailable (%s) — falling back to %r",
                        candidate,
                        exc,
                        candidates[position + 1],
                    )
                    continue

        raise RuntimeError(
            "All configured NIM models failed. Tried: "
            + ", ".join(candidates)
            + f". Last error: {last_error}. Set HECTOR_NIM_GENERATION_MODEL / "
            "HECTOR_NIM_CHAT_MODEL to a working model id "
            "(comma-separated for a fallback chain)."
        ) from last_error

    def chat_json(
        self,
        messages: list[dict],
        temperature: float = 0.0,
        max_tokens: int = 1024,
        model: str | None = None,
        max_attempts: int | None = None,
    ) -> dict:
        """Chat and parse the response as JSON."""
        raw = self.chat(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            model=model,
            max_attempts=max_attempts,
        )
        return json.loads(raw)


# Singleton — created lazily when first accessed
_default_client: NimLLMClient | None = None


def get_nim_llm(**kwargs) -> NimLLMClient:
    """Get or create the default NIM LLM client."""
    global _default_client
    if _default_client is None:
        _default_client = NimLLMClient(**kwargs)
    return _default_client
