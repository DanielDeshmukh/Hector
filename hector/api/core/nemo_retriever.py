"""
Unified NeMo Retriever provider for HECTOR.

Wraps NVIDIA's NeMo Retriever capabilities into a single interface:
- OCR processing via Nemotron OCR API
- Document parsing and intelligent legal-aware chunking
- Embedding generation via Nemotron embeddings
- Reranking via Nemotron reranker

Env vars:
    HECTOR_NEMO_RETRIEVER_ENABLED: "1" to enable (default: "0")
    NVIDIA_API_KEY: Required for all NeMo operations
    HECTOR_NEMO_OCR_MODEL: OCR model (default: "nvidia/nemotron-ocr-v1")
    HECTOR_NEMO_EMBED_MODEL: Embedding model (default: "nvidia/nemotron-embed-4b-v1")
    HECTOR_NEMO_RERANK_MODEL: Rerank model (default: "nvidia/llama-nemotron-rerank-1b-v2")
"""

import base64
import io
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("hector.nemo_retriever")

# Default models
DEFAULT_OCR_MODEL = "nvidia/nemotron-ocr-v1"
DEFAULT_EMBED_MODEL = "nvidia/nemotron-embed-4b-v1"
DEFAULT_RERANK_MODEL = "nvidia/llama-nemotron-rerank-1b-v2"

# API endpoints
NVIDIA_API_BASE = "https://ai.api.nvidia.com/v1"


@dataclass
class NemoOCRResult:
    """Result from OCR processing."""

    text: str
    markdown: str
    confidence: float
    page_number: int
    processing_time_ms: float
    model: str


@dataclass
class NemoChunk:
    """A processed document chunk with metadata."""

    text: str
    metadata: dict[str, Any]
    embedding: list[float] | None = None


@dataclass
class NemoRerankResult:
    """Result from reranking."""

    index: int
    score: float
    text: str
    reasons: list[str] = field(default_factory=list)


class NemoRetrieverProvider:
    """
    Unified provider for NVIDIA NeMo Retriever capabilities.

    Provides OCR, document parsing, chunking, embedding, and reranking
    through a single interface with automatic fallback to local processing.
    """

    def __init__(
        self,
        api_key: str | None = None,
        ocr_model: str | None = None,
        embed_model: str | None = None,
        rerank_model: str | None = None,
    ):
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY", "")
        self.ocr_model = ocr_model or os.getenv(
            "HECTOR_NEMO_OCR_MODEL", DEFAULT_OCR_MODEL
        )
        self.embed_model = embed_model or os.getenv(
            "HECTOR_NEMO_EMBED_MODEL", DEFAULT_EMBED_MODEL
        )
        self.rerank_model = rerank_model or os.getenv(
            "HECTOR_NEMO_RERANK_MODEL", DEFAULT_RERANK_MODEL
        )
        self._available = None  # Lazy health check

    def _check_available(self) -> bool:
        """Check if the NeMo Retriever API is reachable."""
        if self._available is not None:
            return self._available

        if not self.api_key:
            logger.warning("NVIDIA_API_KEY not set — NeMo Retriever unavailable")
            self._available = False
            return False

        try:
            import requests

            resp = requests.get(
                f"{NVIDIA_API_BASE}/chat/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10,
            )
            self._available = resp.status_code in (200, 401, 405)
        except Exception as e:
            logger.warning(f"NeMo Retriever health check failed: {e}")
            self._available = False

        return self._available

    @property
    def is_available(self) -> bool:
        """Check if NeMo Retriever is available."""
        return self._check_available()

    # -------------------------------------------------------------------------
    # OCR
    # -------------------------------------------------------------------------

    def ocr_page(
        self, image_bytes: bytes, page_number: int, dpi: int = 300
    ) -> NemoOCRResult:
        """
        Process a scanned page via Nemotron OCR API.

        Args:
            image_bytes: Raw PNG/JPEG image bytes
            page_number: Page number for tracking
            dpi: DPI used for rendering (affects quality)

        Returns:
            NemoOCRResult with extracted text and metadata
        """
        if not self.api_key:
            raise ValueError("NVIDIA_API_KEY is required for NeMo OCR")

        import requests

        image_b64 = base64.b64encode(image_bytes).decode()
        start = time.perf_counter()

        resp = requests.post(
            f"{NVIDIA_API_BASE}/cv/{self.ocr_model}",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json={
                "image": f"data:image/png;base64,{image_b64}",
                "dpi": dpi,
            },
            timeout=120,
        )
        resp.raise_for_status()
        elapsed_ms = (time.perf_counter() - start) * 1000

        data = resp.json()
        return NemoOCRResult(
            text=data.get("text", ""),
            markdown=data.get("markdown", data.get("text", "")),
            confidence=data.get("confidence", 0.0),
            page_number=page_number,
            processing_time_ms=elapsed_ms,
            model=self.ocr_model,
        )

    def ocr_page_from_pdf(
        self, file_path: str, page_number: int, dpi: int = 300
    ) -> NemoOCRResult:
        """
        Render a PDF page to image and OCR it.

        Args:
            file_path: Path to PDF file
            page_number: 1-indexed page number
            dpi: Render DPI

        Returns:
            NemoOCRResult with extracted text
        """
        try:
            from pdf2image import convert_from_path
        except ImportError:
            raise ImportError(
                "pdf2image is required for PDF OCR: pip install pdf2image"
            )

        poppler_path = os.getenv("HECTOR_POPPLER_PATH") or None
        page_images = convert_from_path(
            file_path,
            dpi=dpi,
            first_page=page_number,
            last_page=page_number,
            poppler_path=poppler_path,
        )
        if not page_images:
            return NemoOCRResult(
                text="",
                markdown="",
                confidence=0.0,
                page_number=page_number,
                processing_time_ms=0.0,
                model=self.ocr_model,
            )

        buf = io.BytesIO()
        page_images[0].save(buf, format="PNG")
        return self.ocr_page(buf.getvalue(), page_number, dpi)

    # -------------------------------------------------------------------------
    # Embedding
    # -------------------------------------------------------------------------

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Embed a batch of documents via Nemotron embedding API.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors (each 2048-dimensional)
        """
        if not self.api_key:
            raise ValueError("NVIDIA_API_KEY is required for NeMo embeddings")

        import requests

        embeddings = []
        for text in texts:
            resp = requests.post(
                f"{NVIDIA_API_BASE}/retrieval/{self.embed_model}",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "input": text,
                    "model": self.embed_model,
                    "input_type": "passage",
                },
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
            embeddings.append(data["data"][0]["embedding"])

        return embeddings

    def embed_query(self, text: str) -> list[float]:
        """
        Embed a single query via Nemotron embedding API.

        Args:
            text: Query text to embed

        Returns:
            Embedding vector (2048-dimensional)
        """
        if not self.api_key:
            raise ValueError("NVIDIA_API_KEY is required for NeMo embeddings")

        import requests

        resp = requests.post(
            f"{NVIDIA_API_BASE}/retrieval/{self.embed_model}",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "input": text,
                "model": self.embed_model,
                "input_type": "query",
            },
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["data"][0]["embedding"]

    # -------------------------------------------------------------------------
    # Reranking
    # -------------------------------------------------------------------------

    def rerank(
        self, query: str, documents: list[dict[str, Any]], top_k: int = 5
    ) -> list[NemoRerankResult]:
        """
        Rerank documents by relevance to query.

        Args:
            query: The search query
            documents: List of dicts with at least 'text' or 'document' key
            top_k: Number of top results to return

        Returns:
            List of NemoRerankResult sorted by relevance
        """
        if not self.api_key:
            raise ValueError("NVIDIA_API_KEY is required for NeMo reranking")

        if not documents:
            return []

        import requests

        # Build passages payload
        passages = []
        for doc in documents:
            text = doc.get("text", doc.get("document", ""))
            passages.append({"text": text})

        resp = requests.post(
            f"{NVIDIA_API_BASE}/retrieval/{self.rerank_model}/reranking",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.rerank_model,
                "query": {"text": query},
                "passages": passages,
                "top_k": top_k,
            },
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()

        results = []
        for rank in data.get("rankings", []):
            idx = rank["index"]
            results.append(
                NemoRerankResult(
                    index=idx,
                    score=rank.get("logit", rank.get("score", 0.0)),
                    text=passages[idx]["text"] if idx < len(passages) else "",
                    reasons=[f"nemotron-reranked (score={rank.get('logit', 0.0):.3f})"],
                )
            )

        return results

    # -------------------------------------------------------------------------
    # Document Processing Pipeline
    # -------------------------------------------------------------------------

    def process_document(
        self,
        file_path: str,
        pages: list[int] | None = None,
        dpi: int = 300,
        chunk_size: int = 800,
        chunk_overlap: int = 150,
    ) -> list[NemoChunk]:
        """
        Full document processing pipeline: OCR → chunk → embed.

        Args:
            file_path: Path to PDF document
            pages: Specific pages to process (None = all)
            dpi: Render DPI for OCR
            chunk_size: Target chunk size in tokens
            chunk_overlap: Overlap between chunks

        Returns:
            List of NemoChunk with text, metadata, and embeddings
        """
        from pypdf import PdfReader

        reader = PdfReader(file_path)
        total_pages = len(reader.pages)
        target_pages = pages or list(range(1, total_pages + 1))

        all_chunks = []

        for page_num in target_pages:
            if page_num < 1 or page_num > total_pages:
                continue

            # Extract text via pypdf first
            page_text = reader.pages[page_num - 1].extract_text() or ""

            # If text extraction yields little content, use OCR
            if len(page_text.strip()) < 50:
                try:
                    ocr_result = self.ocr_page_from_pdf(file_path, page_num, dpi)
                    page_text = ocr_result.markdown or ocr_result.text
                except Exception as e:
                    logger.warning(f"OCR failed for page {page_num}: {e}")
                    continue

            # Chunk the text
            chunks = self._chunk_text(page_text, chunk_size, chunk_overlap)
            for i, chunk_text in enumerate(chunks):
                all_chunks.append(
                    NemoChunk(
                        text=chunk_text,
                        metadata={
                            "source": os.path.basename(file_path),
                            "page": page_num,
                            "chunk_index": i,
                            "total_pages": total_pages,
                            "processing_method": "nemo_retriever",
                        },
                    )
                )

        # Batch embed all chunks
        if all_chunks:
            texts = [c.text for c in all_chunks]
            try:
                embeddings = self.embed_documents(texts)
                for chunk, embedding in zip(all_chunks, embeddings):
                    chunk.embedding = embedding
            except Exception as e:
                logger.warning(f"Batch embedding failed: {e}")

        return all_chunks

    def _chunk_text(
        self, text: str, chunk_size: int = 800, overlap: int = 150
    ) -> list[str]:
        """
        Split text into overlapping chunks.

        Uses sentence boundaries when possible to avoid splitting mid-sentence.
        """
        if not text or len(text.strip()) < 50:
            return []

        # Simple word-based chunking with overlap
        words = text.split()
        if len(words) <= chunk_size // 5:  # Approximate words per chunk
            return [text.strip()]

        chunks = []
        start = 0
        while start < len(words):
            end = min(start + chunk_size // 5, len(words))
            chunk = " ".join(words[start:end])

            # Try to find a sentence boundary near the end
            if end < len(words):
                for sep in [". ", ".\n", "? ", "! ", "\n\n"]:
                    last_sep = chunk.rfind(sep)
                    if last_sep > len(chunk) * 0.5:
                        chunk = chunk[: last_sep + len(sep)].strip()
                        end = start + len(chunk.split())
                        break

            if chunk.strip():
                chunks.append(chunk.strip())

            # Always advance by at least 1 word to prevent infinite loop
            advance = max(end - start - (overlap // 5), 1)
            start += advance
            if start >= len(words):
                break

        return chunks


def get_nemo_retriever(
    api_key: str | None = None,
    **kwargs,
) -> NemoRetrieverProvider | None:
    """
    Factory function to get a NemoRetrieverProvider.

    Returns None if not enabled or API key is missing.
    """
    enabled = os.getenv("HECTOR_NEMO_RETRIEVER_ENABLED", "0") == "1"
    if not enabled:
        return None

    api_key = api_key or os.getenv("NVIDIA_API_KEY", "")
    if not api_key:
        logger.warning("NVIDIA_API_KEY not set — NeMo Retriever disabled")
        return None

    provider = NemoRetrieverProvider(api_key=api_key, **kwargs)
    if not provider.is_available:
        logger.warning(
            "NeMo Retriever API unreachable — falling back to local processing"
        )
        return None

    return provider
