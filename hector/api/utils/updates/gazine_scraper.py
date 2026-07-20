"""
Gazette Scraper for monitoring Indian legal amendments.
Monitors India Gazette (egazette.nic.in) for new BNS/BNSS/BSA amendments.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from datetime import datetime as DT

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)

# Key acts to monitor
ACTS_TO_MONITOR = [
    "Bharatiya Nyaya Sanhita",
    "Bharatiya Nyaya Sanhita 2023",
    "Bharatiya Nagarik Suraksha Sanhita",
    "Bharatiya Nagarik Suraksha Sanhita 2023",
    "Bharatiya Sakshya Adhiniyam",
    "Bharatiya Sakshya Adhiniyam 2023",
    "Indian Penal Code",
    "Code of Criminal Procedure",
    "Indian Evidence Act",
]

NOTIFICATION_TYPES = [
    "Ordinance",
    "Amendment",
    "Notification",
    "Correction",
    "Repeal",
]


class Amendment:
    """Represents a legal amendment from the Gazette."""

    def __init__(
        self,
        act_name: str,
        notification_number: str,
        notification_date: DT,
        title: str,
        description: str,
        url: str,
        sections_affected: list[str] | None = None,
    ):
        self.act_name = act_name
        self.notification_number = notification_number
        self.notification_date = notification_date
        self.title = title
        self.description = description
        self.url = url
        self.sections_affected = sections_affected or []
        self.created_at = datetime.now()

    def to_dict(self) -> dict:
        return {
            "act_name": self.act_name,
            "notification_number": self.notification_number,
            "notification_date": self.notification_date.isoformat(),
            "title": self.title,
            "description": self.description,
            "url": self.url,
            "sections_affected": self.sections_affected,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Amendment":
        return cls(
            act_name=data["act_name"],
            notification_number=data["notification_number"],
            notification_date=datetime.fromisoformat(data["notification_date"]),
            title=data["title"],
            description=data["description"],
            url=data["url"],
            sections_affected=data.get("sections_affected", []),
        )


class GazetteScraper:
    """
    Scraper for monitoring the India Gazette for legal amendments.
    Note: Requires network access to egazette.nic.in
    """

    BASE_URL = "https://egazette.nic.in"
    SEARCH_URL = "https://egazette.nic.in/Search?search_field=All&search_text="

    def __init__(self, cache_dir: Path | None = None):
        self.cache_dir = cache_dir or Path("data/amendments")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.last_checked: datetime | None = None
        self.amendments: list[Amendment] = self._load_cached_amendments()

    def _load_cached_amendments(self) -> list[Amendment]:
        """Load amendments from cache file."""
        cache_file = self.cache_dir / "amendments.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r") as f:
                    data = json.load(f)
                    return [Amendment.from_dict(d) for d in data]
            except (json.JSONDecodeError, KeyError):
                return []
        return []

    def _save_amendments(self) -> None:
        """Save amendments to cache file."""
        cache_file = self.cache_dir / "amendments.json"
        with open(cache_file, "w") as f:
            json.dump([a.to_dict() for a in self.amendments], f, indent=2)

    async def check_latest_amendments(
        self,
        days_back: int = 30,
    ) -> list[Amendment]:
        """
        Check for the latest amendments to monitored acts.
        Returns list of new amendments since last check.
        """
        new_amendments: list[Amendment] = []
        cutoff = datetime.now() - timedelta(days=days_back)

        try:
            async with httpx.AsyncClient(
                timeout=30.0,
                headers={"User-Agent": USER_AGENT},
                follow_redirects=True,
            ) as client:
                for act_name in ACTS_TO_MONITOR:
                    try:
                        resp = await client.get(
                            self.SEARCH_URL,
                            params={"search_field": "All", "search_text": act_name},
                        )
                        resp.raise_for_status()
                        entries = self._parse_gazette_entries(
                            resp.text, act_name, cutoff
                        )
                        new_amendments.extend(entries)
                    except httpx.HTTPError as exc:
                        logger.warning(
                            "HTTP error fetching gazette for %s: %s", act_name, exc
                        )
                    except httpx.TimeoutException as exc:
                        logger.warning(
                            "Timeout fetching gazette for %s: %s", act_name, exc
                        )
        except Exception as exc:
            logger.warning("Failed to initialise HTTP client: %s", exc)

        self.last_checked = datetime.now()

        if new_amendments:
            self.amendments.extend(new_amendments)
            self._save_amendments()

        return new_amendments

    def _parse_gazette_entries(
        self,
        html: str,
        act_name: str,
        cutoff: datetime,
    ) -> list[Amendment]:
        """Parse gazette HTML and extract amendment entries."""
        entries: list[Amendment] = []

        row_pattern = re.compile(r"<tr[^>]*>(.*?)</tr>", re.DOTALL | re.IGNORECASE)
        cell_pattern = re.compile(r"<td[^>]*>(.*?)</td>", re.DOTALL | re.IGNORECASE)
        link_pattern = re.compile(
            r'<a[^>]+href="([^"]*)"[^>]*>(.*?)</a>', re.DOTALL | re.IGNORECASE
        )
        date_pattern = re.compile(r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})")

        for row_match in row_pattern.finditer(html):
            row_html = row_match.group(1)
            cells = cell_pattern.findall(row_html)
            if len(cells) < 3:
                continue

            raw_title = re.sub(r"<[^>]+>", "", cells[0]).strip()
            raw_date = re.sub(r"<[^>]+>", "", cells[1]).strip()
            raw_desc = re.sub(r"<[^>]+>", "", cells[2]).strip()

            title = re.sub(r"\s+", " ", raw_title)
            description = re.sub(r"\s+", " ", raw_desc)

            date_match = date_pattern.search(raw_date)
            if not date_match:
                continue
            try:
                entry_date = datetime.strptime(date_match.group(1), "%d-%m-%Y")
            except ValueError:
                try:
                    entry_date = datetime.strptime(date_match.group(1), "%d/%m/%Y")
                except ValueError:
                    continue

            if entry_date < cutoff:
                continue

            url = self.BASE_URL
            link_match = link_pattern.search(row_html)
            if link_match:
                href = link_match.group(1)
                if href.startswith("/"):
                    url = self.BASE_URL + href
                elif href.startswith("http"):
                    url = href

            entry = Amendment(
                act_name=act_name,
                notification_number=title[:50],
                notification_date=entry_date,
                title=title,
                description=description,
                url=url,
                sections_affected=[],
            )
            entries.append(entry)

        return entries

    def get_amendments_for_act(self, act_name: str) -> list[Amendment]:
        """Get all amendments for a specific act."""
        return [a for a in self.amendments if a.act_name == act_name]

    def get_recent_amendments(self, days: int = 30) -> list[Amendment]:
        """Get amendments from the last N days."""
        cutoff = datetime.now() - timedelta(days=days)
        return [a for a in self.amendments if a.notification_date >= cutoff]

    def needs_reindex(self, act_name: str) -> bool:
        """Check if an act needs re-indexing based on recent amendments."""
        recent = self.get_recent_amendments(days=30)
        return any(a.act_name == act_name for a in recent)


class AmendmentTracker:
    """Tracks amendment history for legal acts."""

    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or Path("data/amendments/tracker.json")
        self.history: list[dict] = []
        self._load_history()

    def _load_history(self) -> None:
        if self.db_path.exists():
            try:
                with open(self.db_path, "r") as f:
                    self.history = json.load(f)
            except (json.JSONDecodeError, KeyError):
                self.history = []

    def _save_history(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.db_path, "w") as f:
            json.dump(self.history, f, indent=2)

    def record_amendment(self, act: str, section: str, amendment: Amendment) -> None:
        """Record a new amendment in history."""
        self.history.append(
            {
                "act": act,
                "section": section,
                "amendment": amendment.to_dict(),
                "recorded_at": datetime.now().isoformat(),
            }
        )
        self._save_history()

    def get_amendment_history(
        self,
        act: str,
        section: str | None = None,
    ) -> list[dict]:
        """Get amendment history for an act or specific section."""
        filtered = [h for h in self.history if h["act"] == act]
        if section:
            filtered = [h for h in filtered if h["section"] == section]
        return filtered

    def get_all_acts_with_amendments(self) -> list[str]:
        """Get list of all acts that have amendments recorded."""
        return list(set(h["act"] for h in self.history))


class AmendmentAlert:
    """Handles alerts for new amendments."""

    def __init__(self, scraper: GazetteScraper):
        self.scraper = scraper
        self.alert_rules: list[dict] = []

    def add_rule(self, act_name: str, alert_type: str, recipients: list[str]) -> None:
        """Add an alert rule for an act."""
        self.alert_rules.append(
            {
                "act_name": act_name,
                "alert_type": alert_type,
                "recipients": recipients,
                "created_at": datetime.now().isoformat(),
            }
        )

    def check_and_alert(self) -> list[dict]:
        """Check for new amendments and trigger alerts."""
        alerts = []
        new_amendments = self.scraper.get_recent_amendments(days=7)

        for amendment in new_amendments:
            for rule in self.alert_rules:
                if rule["act_name"] == amendment.act_name:
                    alert = {
                        "amendment": amendment.to_dict(),
                        "alert_type": rule["alert_type"],
                        "recipients": rule["recipients"],
                        "triggered_at": datetime.now().isoformat(),
                    }
                    alerts.append(alert)

        return alerts
