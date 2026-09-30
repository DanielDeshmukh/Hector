"""
NVIDIA NIM LLM Client.
Wraps the NIM OpenAI-compatible API for chat completions.
Used for intent routing and response generation.
"""

import json
import logging
import os

from dotenv import load_dotenv

from utils.retry import retry

load_dotenv()

logger = logging.getLogger("hector.nim_llm")

NIM_BASE_URL = os.getenv("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
NIM_API_KEY = os.getenv("NIM_API_KEY") or os.getenv("NVIDIA_API_KEY")
DEFAULT_CHAT_MODEL = os.getenv("HECTOR_NIM_CHAT_MODEL", "meta/llama-3.1-8b-instruct")

# Model registry — different models for different pipeline stages.
# Each env value may be a comma-separated fallback chain (tried in order).
NIM_MODELS = {
    "router": os.getenv("HECTOR_NIM_ROUTER_MODEL", "meta/llama-3.1-8b-instruct"),
    "generation": os.getenv(
        "HECTOR_NIM_GENERATION_MODEL", "meta/llama-3.1-8b-instruct"
    ),
    "verification": os.getenv(
        "HECTOR_NIM_VERIFICATION_MODEL", "meta/llama-3.1-8b-instruct"
    ),
    "query_intelligence": os.getenv(
        "HECTOR_NIM_QI_MODEL", "nvidia/llama-3.1-nemotron-nano-8b-v1"
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
                response = retry(
                    client.chat.completions.create,
                    max_attempts=3,
                    operation_name=f"nim_chat[{candidate}]",
                    **kwargs,
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
    ) -> dict:
        """Chat and parse the response as JSON."""
        raw = self.chat(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            model=model,
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
