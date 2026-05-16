"""
Partial Re-indexing Script for Layer 2 (Amendment) data.
Only re-indexes new amendments without re-processing the entire corpus.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from data.hybrid_retriever import HectorHybridRetriever


class PartialReindexer:
    """
    Handles partial re-indexing for new amendments.
    Supports Layer 1 (full index) and Layer 2 (amendments only).
    """

    def __init__(self, retriever: "HectorHybridRetriever"):
        self.retriever = retriever
        self.last_full_reindex: datetime | None = None
        self.last_partial_reindex: datetime | None = None

    def should_full_reindex(self) -> bool:
        """Check if a full re-index is due (quarterly)."""
        if not self.last_full_reindex:
            return True

        days_since = (datetime.now() - self.last_full_reindex).days
        return days_since >= 90  # Quarterly

    def should_partial_reindex(self) -> bool:
        """Check if a partial re-index is due (monthly)."""
        if not self.last_partial_reindex:
            return True

        days_since = (datetime.now() - self.last_partial_reindex).days
        return days_since >= 30  # Monthly

    def reindex_amendments(self, amendments: list[dict]) -> dict:
        """
        Re-index only the new amendments.
        Returns statistics about the re-indexing operation.
        """
        stats = {
            "started_at": datetime.now(),
            "amendments_processed": 0,
            "chunks_indexed": 0,
            "errors": [],
        }

        for amendment in amendments:
            try:
                # TODO: Extract text for the amendment
                # TODO: Chunk the text appropriately
                # TODO: Add to vector database with special metadata
                # TODO: Mark as "amendment" type for Layer 2

                stats["amendments_processed"] += 1
                stats["chunks_indexed"] += len(amendment.get("chunks", []))
            except Exception as e:
                stats["errors"].append({
                    "amendment_id": amendment.get("id"),
                    "error": str(e),
                })

        stats["completed_at"] = datetime.now()
        self.last_partial_reindex = datetime.now()

        return stats

    def reindex_full(self) -> dict:
        """Perform a full re-index of the entire corpus."""
        stats = {
            "started_at": datetime.now(),
            "documents_processed": 0,
            "chunks_indexed": 0,
            "errors": [],
        }

        # TODO: Implement full corpus re-indexing
        # This would involve:
        # 1. Clearing existing index
        # 2. Re-processing all source documents
        # 3. Updating all metadata

        stats["completed_at"] = datetime.now()
        self.last_full_reindex = datetime.now()

        return stats

    def get_index_statistics(self) -> dict:
        """Get current index statistics."""
        return {
            "total_records": len(getattr(self.retriever, "records", [])),
            "last_full_reindex": self.last_full_reindex,
            "last_partial_reindex": self.last_partial_reindex,
            "should_full_reindex": self.should_full_reindex(),
            "should_partial_reindex": self.should_partial_reindex(),
        }


def create_reindex_job(amendments: list[dict], mode: str = "partial") -> dict:
    """Create a reindex job configuration."""
    return {
        "mode": mode,  # "full" or "partial"
        "amendments": amendments,
        "created_at": datetime.now(),
        "status": "pending",
    }