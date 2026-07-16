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

# Model registry — different models for different pipeline stages
NIM_MODELS = {
    "router": os.getenv("HECTOR_NIM_ROUTER_MODEL", "meta/llama-3.1-8b-instruct"),
    "generation": os.getenv(
        "HECTOR_NIM_GENERATION_MODEL", "meta/llama-3.1-8b-instruct"
    ),
    "verification": os.getenv(
        "HECTOR_NIM_VERIFICATION_MODEL", "meta/llama-3.1-8b-instruct"
    ),
}


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
            model: Override model for this call.

        Returns:
            The assistant message content string.
        """
        client = self._get_client()
        kwargs = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            kwargs["response_format"] = response_format

        response = retry(
            client.chat.completions.create,
            max_attempts=3,
            operation_name="nim_chat",
            **kwargs,
        )
        return response.choices[0].message.content

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
