"""
Partial Re-indexing Script for Layer 2 (Amendment) data.
Only re-indexes new amendments without re-processing the entire corpus.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from data.hybrid_retriever import HectorHybridRetriever

logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOKS_DIR = os.getenv("HECTOR_BOOKS_DIR", os.path.join(PROJECT_ROOT, "data", "Books"))


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

        Each amendment dict should contain:
            - id: unique identifier
            - text: amendment text
            - source: source PDF filename
            - chunks: optional pre-chunked text list
            - metadata: optional dict with additional metadata
        """
        stats = {
            "started_at": datetime.now().isoformat(),
            "amendments_processed": 0,
            "chunks_indexed": 0,
            "errors": [],
        }

        collection = self.retriever.collection
        if collection is None:
            stats["errors"].append({"error": "No ChromaDB collection available"})
            stats["completed_at"] = datetime.now().isoformat()
            return stats

        from utils.enhanced_ingestor import EnhancedHectorIngestor
        ingestor = EnhancedHectorIngestor(reindex_mode=True)

        for amendment in amendments:
            try:
                text = amendment.get("text", "")
                if not text:
                    stats["errors"].append({
                        "amendment_id": amendment.get("id"),
                        "error": "No text provided",
                    })
                    continue

                source = amendment.get("source", "amendment")
                amendment_id = amendment.get("id", str(uuid.uuid4()))
                amendment_metadata = amendment.get("metadata", {})

                existing_chunks = amendment.get("chunks")
                if existing_chunks:
                    chunk_texts = existing_chunks
                else:
                    chunk_texts = ingestor.chunk_text(text)

                if not chunk_texts:
                    stats["errors"].append({
                        "amendment_id": amendment_id,
                        "error": "No chunks produced from text",
                    })
                    continue

                documents = []
                metadatas = []
                ids = []

                for chunk_index, chunk in enumerate(chunk_texts):
                    chunk_id = f"amendment_{amendment_id}_chunk_{chunk_index}"
                    page_hash = ingestor.get_page_hash(source, chunk_index)

                    base_metadata = {
                        "source": source,
                        "page": 0,
                        "page_hash": page_hash,
                        "chunk_index": chunk_index,
                        "ingested_at": str(datetime.now()),
                        "mapping_accuracy": "amendment_v1",
                        "content_type": "amendment",
                        "amendment_id": amendment_id,
                    }
                    base_metadata.update(amendment_metadata)

                    documents.append(chunk)
                    metadatas.append(base_metadata)
                    ids.append(chunk_id)

                collection.upsert(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids,
                )

                stats["amendments_processed"] += 1
                stats["chunks_indexed"] += len(documents)

            except Exception as e:
                logger.error("Error indexing amendment %s: %s", amendment.get("id"), e)
                stats["errors"].append({
                    "amendment_id": amendment.get("id"),
                    "error": str(e),
                })

        stats["completed_at"] = datetime.now().isoformat()
        self.last_partial_reindex = datetime.now()
        self._save_last_reindex("partial", datetime.now())
        self.retriever.refresh_index()

        return stats

    def reindex_full(self) -> dict:
        """
        Perform a full re-index of the entire corpus.
        Clears existing ChromaDB collection and re-processes all PDFs.
        """
        logger.info("Starting full re-index of corpus.")
        stats = {
            "status": "running",
            "started_at": datetime.now().isoformat(),
            "reindexed_count": 0,
            "errors": [],
            "timestamp": datetime.now().isoformat(),
        }

        try:
            collection = self.retriever.collection
            if collection is None:
                stats["status"] = "failed"
                stats["errors"].append("No ChromaDB collection available")
                return stats

            existing = collection.get()
            if existing["ids"]:
                collection.delete(ids=existing["ids"])
                logger.info("Cleared %d existing records from collection.", len(existing["ids"]))

            from utils.enhanced_ingestor import EnhancedHectorIngestor, BOOKS_DIR as INGESTOR_BOOKS_DIR

            books_dir = Path(INGESTOR_BOOKS_DIR)
            if not books_dir.exists():
                stats["status"] = "failed"
                stats["errors"].append(f"Books directory not found: {books_dir}")
                return stats

            pdf_files = list(books_dir.glob("*.pdf"))
            if not pdf_files:
                stats["status"] = "completed"
                stats["errors"].append("No PDF files found in books directory")
                return stats

            ingestor = EnhancedHectorIngestor(reindex_mode=True)
            total_chunks = 0

            for pdf_path in pdf_files:
                try:
                    result = ingestor.process_book(pdf_path.name, str(pdf_path))
                    total_chunks += result.get("chunks", 0)
                    stats["reindexed_count"] += 1
                    logger.info("Re-indexed %s: %d chunks", pdf_path.name, result.get("chunks", 0))
                except Exception as e:
                    logger.error("Error re-indexing %s: %s", pdf_path.name, e)
                    stats["errors"].append({"file": pdf_path.name, "error": str(e)})

            stats["chunks_indexed"] = total_chunks
            stats["status"] = "completed"

            self.last_full_reindex = datetime.now()
            self._save_last_reindex("full", datetime.now())
            self.retriever.refresh_index()
            logger.info("Full re-index completed. %d files, %d chunks total.", stats["reindexed_count"], total_chunks)

        except Exception as e:
            logger.error("Full re-index failed: %s", e)
            stats["status"] = "failed"
            stats["errors"].append(str(e))

        stats["completed_at"] = datetime.now().isoformat()
        stats["timestamp"] = datetime.now().isoformat()
        return stats

    def reindex_incremental(self, days: int = 7) -> dict:
        """
        Perform an incremental re-index for recent changes.
        Finds PDFs modified in the last N days and re-indexes them.
        """
        logger.info("Starting incremental re-index for files modified in last %d days.", days)
        stats = {
            "status": "running",
            "started_at": datetime.now().isoformat(),
            "reindexed_count": 0,
            "errors": [],
            "timestamp": datetime.now().isoformat(),
        }

        try:
            collection = self.retriever.collection
            if collection is None:
                stats["status"] = "failed"
                stats["errors"].append("No ChromaDB collection available")
                return stats

            from utils.enhanced_ingestor import BOOKS_DIR as INGESTOR_BOOKS_DIR

            books_dir = Path(INGESTOR_BOOKS_DIR)
            if not books_dir.exists():
                stats["status"] = "failed"
                stats["errors"].append(f"Books directory not found: {books_dir}")
                return stats

            cutoff = datetime.now() - timedelta(days=days)
            pdf_files = [
                f for f in books_dir.glob("*.pdf")
                if datetime.fromtimestamp(f.stat().st_mtime) >= cutoff
            ]

            if not pdf_files:
                stats["status"] = "completed"
                stats["chunks_indexed"] = 0
                return stats

            from utils.enhanced_ingestor import EnhancedHectorIngestor
            ingestor = EnhancedHectorIngestor(reindex_mode=True)
            total_chunks = 0

            for pdf_path in pdf_files:
                try:
                    filename = pdf_path.name

                    existing = collection.get(where={"source": filename})
                    if existing["ids"]:
                        collection.delete(ids=existing["ids"])

                    result = ingestor.process_book(filename, str(pdf_path))
                    total_chunks += result.get("chunks", 0)
                    stats["reindexed_count"] += 1
                    logger.info("Re-indexed %s: %d chunks", filename, result.get("chunks", 0))
                except Exception as e:
                    logger.error("Error re-indexing %s: %s", pdf_path.name, e)
                    stats["errors"].append({"file": pdf_path.name, "error": str(e)})

            stats["chunks_indexed"] = total_chunks
            stats["status"] = "completed"

            self.last_incremental = datetime.now()
            self._save_last_reindex("incremental", datetime.now())
            self.retriever.refresh_index()
            logger.info("Incremental re-index completed. %d files, %d chunks.", stats["reindexed_count"], total_chunks)

        except Exception as e:
            logger.error("Incremental re-index failed: %s", e)
            stats["status"] = "failed"
            stats["errors"].append(str(e))

        stats["completed_at"] = datetime.now().isoformat()
        stats["timestamp"] = datetime.now().isoformat()
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
        """
        Rollback to a specific version by restoring index state from backup.
        Returns stats dict with status, version, restored_count, timestamp.
        """
        logger.info("Attempting rollback to version: %s", version_name)
        stats = {
            "status": "running",
            "version": version_name,
            "restored_count": 0,
            "timestamp": datetime.now().isoformat(),
        }

        try:
            version_file = self.versions_dir / f"{version_name}.json"
            if not version_file.exists():
                stats["status"] = "error"
                stats["error"] = f"Version '{version_name}' not found"
                logger.error("Version not found: %s", version_name)
                return stats

            with open(version_file, "r") as f:
                version_data = json.load(f)

            metadata = version_data.get("metadata", {})
            source_index = metadata.get("index_path")
            collection_name = metadata.get("collection_name", "indian_law_bns")

            if source_index and os.path.exists(source_index):
                import shutil

                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                db_path = os.path.join(project_root, "hector_db")
                target_collection_dir = os.path.join(db_path, collection_name)

                if os.path.isdir(target_collection_dir):
                    shutil.rmtree(target_collection_dir)

                shutil.copytree(source_index, target_collection_dir)
                stats["restored_count"] = 1
                logger.info("Restored index from backup: %s", source_index)
            else:
                backup_files = metadata.get("files", [])
                restored = 0
                for file_info in backup_files:
                    src = file_info.get("source_path")
                    dst = file_info.get("dest_path")
                    if src and dst and os.path.exists(src):
                        os.makedirs(os.path.dirname(dst), exist_ok=True)
                        shutil.copy2(src, dst)
                        restored += 1
                stats["restored_count"] = restored
                logger.info("Restored %d files from version %s", restored, version_name)

            stats["status"] = "completed"

        except Exception as e:
            logger.error("Rollback to version %s failed: %s", version_name, e)
            stats["status"] = "error"
            stats["error"] = str(e)

        stats["completed_at"] = datetime.now().isoformat()
        stats["timestamp"] = datetime.now().isoformat()
        return stats