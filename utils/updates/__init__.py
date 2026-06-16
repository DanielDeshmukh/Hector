"""
HECTOR Live Update & Maintenance Pipeline

This module provides:
- GazetteScraper: Monitor India Gazette for legal amendments
- PartialReindexer: Re-index only new amendments (Layer 2)
- AmendmentTracker: Track amendment history for legal acts
- VersionManager: Version rollback capability
"""

from .gazine_scraper import (
    GazetteScraper,
    Amendment,
    AmendmentTracker,
    AmendmentAlert,
    ACTS_TO_MONITOR,
    NOTIFICATION_TYPES,
)
from .reindexer import (
    PartialReindexer,
    ReindexJob,
    ReindexMode,
    VersionManager,
    create_reindex_job,
)

__all__ = [
    # Scraper
    "GazetteScraper",
    "Amendment",
    "AmendmentTracker",
    "AmendmentAlert",
    "ACTS_TO_MONITOR",
    "NOTIFICATION_TYPES",
    # Reindexer
    "PartialReindexer",
    "ReindexJob",
    "ReindexMode",
    "VersionManager",
    "create_reindex_job",
]
