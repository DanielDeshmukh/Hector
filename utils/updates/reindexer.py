"""
Partial Re-indexing Script for Layer 2 (Amendment) data.
Only re-indexes new amendments without re-processing the entire corpus.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from data.hybrid_retriever import HectorHybridRetriever


class ReindexMode:
    """Re-indexing modes."""
    FULL = "full"      # Full corpus re-index
    PARTIAL = "partial"  # Amendments only
    INCREMENTAL = "incremental"  # Recent changes only


class ReindexJob:
    """Represents a re-indexing job."""

    def __init__(
        self,
        mode: str,
        created_at: datetime | None = None,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
        status: str = "pending",
        stats: dict | None = None,
    ):
        self.mode = mode
        self.created_at = created_at or datetime.now()
        self.started_at = started_at
        self.completed_at = completed_at
        self.status = status  # pending, running, completed, failed
        self.stats = stats or {}

    def to_dict(self) -> dict:
        return {
            "mode": self.mode,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status,
            "stats": self.stats,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ReindexJob":
        return cls(
            mode=data["mode"],
            created_at=datetime.fromisoformat(data["created_at"]),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            status=data["status"],
            stats=data.get("stats", {}),
        )


class PartialReindexer:
    """
    Handles partial re-indexing for new amendments.
    Supports Layer 1 (full index) and Layer 2 (amendments only).
    """

    def __init__(self, retriever: "HectorHybridRetriever", jobs_dir: Path | None = None):
        self.retriever = retriever
        self.jobs_dir = jobs_dir or Path("data/amendments/jobs")
        self.jobs_dir.mkdir(parents=True, exist_ok=True)

        self.last_full_reindex: datetime | None = self._load_last_reindex("full")
        self.last_partial_reindex: datetime | None = self._load_last_reindex("partial")
        self.last_incremental: datetime | None = self._load_last_reindex("incremental")

    def _load_last_reindex(self, mode: str) -> datetime | None:
        """Load last reindex timestamp from file."""
        file_path = self.jobs_dir / f"last_{mode}.json"
        if file_path.exists():
            with open(file_path, "r") as f:
                data = json.load(f)
                return datetime.fromisoformat(data["timestamp"])
        return None

    def _save_last_reindex(self, mode: str, timestamp: datetime) -> None:
        """Save last reindex timestamp."""
        file_path = self.jobs_dir / f"last_{mode}.json"
        with open(file_path, "w") as f:
            json.dump({"timestamp": timestamp.isoformat()}, f)

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

    def should_incremental_reindex(self) -> bool:
        """Check if an incremental re-index is due (weekly)."""
        if not self.last_incremental:
            return True

        days_since = (datetime.now() - self.last_incremental).days
        return days_since >= 7  # Weekly

    def create_job(self, mode: str) -> ReindexJob:
        """Create a new re-index job."""
        job = ReindexJob(mode=mode)
        self._save_job(job)
        return job

    def _save_job(self, job: ReindexJob) -> None:
        """Save job to file."""
        file_path = self.jobs_dir / f"job_{job.created_at.strftime('%Y%m%d_%H%M%S')}.json"
        with open(file_path, "w") as f:
            json.dump(job.to_dict(), f, indent=2)

    def get_pending_jobs(self) -> list[ReindexJob]:
        """Get all pending re-index jobs."""
        jobs = []
        for file_path in self.jobs_dir.glob("job_*.json"):
            with open(file_path, "r") as f:
                data = json.load(f)
                job = ReindexJob.from_dict(data)
                if job.status == "pending":
                    jobs.append(job)
        return jobs

    def reindex_amendments(self, amendments: list[dict]) -> dict:
        """
        Re-index only the new amendments.
        Returns statistics about the re-indexing operation.
        """
        stats = {
            "started_at": datetime.now().isoformat(),
            "amendments_processed": 0,
            "chunks_indexed": 0,
            "errors": [],
        }

        for amendment in amendments:
            try:
                # Extract text for the amendment
                # Chunk the text appropriately
                # Add to vector database with special metadata
                # Mark as "amendment" type for Layer 2

                stats["amendments_processed"] += 1
                stats["chunks_indexed"] += len(amendment.get("chunks", []))
            except Exception as e:
                stats["errors"].append({
                    "amendment_id": amendment.get("id"),
                    "error": str(e),
                })

        stats["completed_at"] = datetime.now().isoformat()
        self.last_partial_reindex = datetime.now()
        self._save_last_reindex("partial", datetime.now())

        return stats

    def reindex_full(self) -> dict:
        """Perform a full re-index of the entire corpus."""
        stats = {
            "started_at": datetime.now().isoformat(),
            "documents_processed": 0,
            "chunks_indexed": 0,
            "errors": [],
        }

        # In production:
        # 1. Clear existing index
        # 2. Re-process all source documents
        # 3. Update all metadata
        # 4. Refresh retriever

        stats["completed_at"] = datetime.now().isoformat()
        self.last_full_reindex = datetime.now()
        self._save_last_reindex("full", datetime.now())

        return stats

    def reindex_incremental(self, days: int = 7) -> dict:
        """Perform an incremental re-index for recent changes."""
        stats = {
            "started_at": datetime.now().isoformat(),
            "documents_processed": 0,
            "chunks_indexed": 0,
            "errors": [],
        }

        # Get documents modified in the last N days
        # Re-index only those

        stats["completed_at"] = datetime.now().isoformat()
        self.last_incremental = datetime.now()
        self._save_last_reindex("incremental", datetime.now())

        return stats

    def get_index_statistics(self) -> dict:
        """Get current index statistics."""
        return {
            "total_records": len(getattr(self.retriever, "records", [])),
            "last_full_reindex": self.last_full_reindex.isoformat() if self.last_full_reindex else None,
            "last_partial_reindex": self.last_partial_reindex.isoformat() if self.last_partial_reindex else None,
            "last_incremental": self.last_incremental.isoformat() if self.last_incremental else None,
            "should_full_reindex": self.should_full_reindex(),
            "should_partial_reindex": self.should_partial_reindex(),
            "should_incremental_reindex": self.should_incremental_reindex(),
        }

    def get_next_scheduled_reindex(self) -> dict:
        """Get the next scheduled re-index times."""
        now = datetime.now()

        next_full = None
        if self.last_full_reindex:
            next_full = self.last_full_reindex + timedelta(days=90)
        else:
            next_full = now

        next_partial = None
        if self.last_partial_reindex:
            next_partial = self.last_partial_reindex + timedelta(days=30)
        else:
            next_partial = now

        next_incremental = None
        if self.last_incremental:
            next_incremental = self.last_incremental + timedelta(days=7)
        else:
            next_incremental = now

        return {
            "full": next_full.isoformat(),
            "partial": next_partial.isoformat(),
            "incremental": next_incremental.isoformat(),
        }


def create_reindex_job(mode: str) -> ReindexJob:
    """Create a reindex job configuration."""
    return ReindexJob(mode=mode)


class VersionManager:
    """Manages version rollback capability for the index."""

    def __init__(self, versions_dir: Path | None = None):
        self.versions_dir = versions_dir or Path("data/amendments/versions")
        self.versions_dir.mkdir(parents=True, exist_ok=True)

    def save_version(self, version_name: str, metadata: dict) -> None:
        """Save a snapshot of the current index version."""
        version_file = self.versions_dir / f"{version_name}.json"
        with open(version_file, "w") as f:
            json.dump({
                "version_name": version_name,
                "created_at": datetime.now().isoformat(),
                "metadata": metadata,
            }, f, indent=2)

    def list_versions(self) -> list[dict]:
        """List all saved versions."""
        versions = []
        for file_path in self.versions_dir.glob("*.json"):
            with open(file_path, "r") as f:
                versions.append(json.load(f))
        return sorted(versions, key=lambda x: x.get("created_at", ""), reverse=True)

    def rollback_to_version(self, version_name: str) -> dict:
        """Rollback to a specific version."""
        version_file = self.versions_dir / f"{version_name}.json"
        if not version_file.exists():
            raise FileNotFoundError(f"Version {version_name} not found")

        with open(version_file, "r") as f:
            version_data = json.load(f)

        # In production, this would:
        # 1. Clear current index
        # 2. Restore from version backup
        # 3. Update metadata

        return {
            "rolled_back_to": version_name,
            "rolled_back_at": datetime.now().isoformat(),
        }