"""
Audit Logging for HECTOR Enterprise.
Provides comprehensive audit trails for all operations.
"""

from __future__ import annotations
import json
import time
import threading
from dataclasses import dataclass, field, asdict
from typing import Any, Callable
from enum import Enum
from pathlib import Path
import hashlib
import os


class AuditEventType(Enum):
    """Types of audit events."""
    # Authentication
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    API_KEY_CREATED = "api_key_created"
    API_KEY_REVOKED = "api_key_revoked"

    # Data Access
    SEARCH = "search"
    DOCUMENT_ACCESSED = "document_accessed"
    EXPORT = "export"
    DOWNLOAD = "download"

    # Data Modification
    DOCUMENT_UPLOADED = "document_uploaded"
    DOCUMENT_DELETED = "document_deleted"
    INDEX_UPDATED = "index_updated"
    CONFIG_CHANGED = "config_changed"

    # Administrative
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    ROLE_CHANGED = "role_changed"
    WORKSPACE_CREATED = "workspace_created"
    WORKSPACE_DELETED = "workspace_deleted"

    # Security
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    PERMISSION_DENIED = "permission_denied"

    # System
    SYSTEM_ERROR = "system_error"
    SERVICE_STARTED = "service_started"
    SERVICE_STOPPED = "service_stopped"


class AuditSeverity(Enum):
    """Severity levels for audit events."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Represents an audit event."""
    event_id: str
    timestamp: float
    event_type: str
    severity: str
    user_id: str | None
    username: str | None
    ip_address: str | None
    user_agent: str | None
    resource: str | None
    action: str
    result: str  # success, failure, partial
    details: dict = field(default_factory=dict)
    session_id: str | None = None
    workspace_id: str | None = None


class AuditLogger:
    """Comprehensive audit logger."""

    def __init__(self, log_dir: str | None = None):
        self.log_dir = log_dir or self._get_default_log_dir()
        self._ensure_log_dir()
        self._lock = threading.Lock()
        self._event_count = 0

    def _get_default_log_dir(self) -> str:
        """Get default log directory."""
        return os.path.join(
            os.path.dirname(__file__), "..", "..", "logs", "audit"
        )

    def _ensure_log_dir(self) -> None:
        """Ensure log directory exists."""
        os.makedirs(self.log_dir, exist_ok=True)

    def _generate_event_id(self) -> str:
        """Generate unique event ID."""
        timestamp = str(time.time())
        random_part = os.urandom(8).hex()
        return hashlib.sha256(f"{timestamp}{random_part}".encode()).hexdigest()[:16]

    def _get_current_file(self) -> str:
        """Get current log file based on date."""
        date_str = time.strftime("%Y-%m-%d")
        return os.path.join(self.log_dir, f"audit_{date_str}.jsonl")

    def log(
        self,
        event_type: AuditEventType,
        severity: AuditSeverity,
        action: str,
        result: str = "success",
        user_id: str | None = None,
        username: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        resource: str | None = None,
        details: dict | None = None,
        session_id: str | None = None,
        workspace_id: str | None = None
    ) -> str:
        """Log an audit event."""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            timestamp=time.time(),
            event_type=event_type.value,
            severity=severity.value,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            resource=resource,
            action=action,
            result=result,
            details=details or {},
            session_id=session_id,
            workspace_id=workspace_id
        )

        return self._write_event(event)

    def _write_event(self, event: AuditEvent) -> str:
        """Write event to log file."""
        with self._lock:
            log_file = self._get_current_file()

            try:
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(asdict(event)) + "\n")
                self._event_count += 1
            except Exception as e:
                print(f"[!] Failed to write audit log: {e}")

            return event.event_id

    def log_login(
        self,
        user_id: str,
        username: str,
        ip_address: str,
        success: bool,
        session_id: str | None = None
    ) -> str:
        """Log a login attempt."""
        return self.log(
            event_type=AuditEventType.LOGIN if success else AuditEventType.LOGIN_FAILED,
            severity=AuditSeverity.INFO if success else AuditSeverity.WARNING,
            action="user_login",
            result="success" if success else "failure",
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            session_id=session_id
        )

    def log_search(
        self,
        user_id: str,
        username: str,
        query: str,
        results_count: int,
        ip_address: str | None = None
    ) -> str:
        """Log a search operation."""
        return self.log(
            event_type=AuditEventType.SEARCH,
            severity=AuditSeverity.INFO,
            action="search",
            result="success",
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            details={
                "query": query[:500],  # Truncate long queries
                "results_count": results_count
            }
        )

    def log_document_access(
        self,
        user_id: str,
        document_id: str,
        action: str,
        ip_address: str | None = None
    ) -> str:
        """Log document access."""
        return self.log(
            event_type=AuditEventType.DOCUMENT_ACCESSED,
            severity=AuditSeverity.INFO,
            action=action,
            result="success",
            user_id=user_id,
            resource=document_id,
            ip_address=ip_address
        )

    def log_rate_limit_exceeded(
        self,
        client_id: str,
        ip_address: str,
        limit_type: str,
        details: dict | None = None
    ) -> str:
        """Log rate limit exceeded."""
        return self.log(
            event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
            severity=AuditSeverity.WARNING,
            action="rate_limit_exceeded",
            result="blocked",
            user_id=client_id,
            ip_address=ip_address,
            details=details or {"limit_type": limit_type}
        )

    def log_permission_denied(
        self,
        user_id: str,
        resource: str,
        required_permission: str,
        ip_address: str | None = None
    ) -> str:
        """Log permission denied."""
        return self.log(
            event_type=AuditEventType.PERMISSION_DENIED,
            severity=AuditSeverity.WARNING,
            action="permission_denied",
            result="denied",
            user_id=user_id,
            resource=resource,
            ip_address=ip_address,
            details={"required_permission": required_permission}
        )

    def log_config_change(
        self,
        user_id: str,
        config_key: str,
        old_value: Any,
        new_value: Any
    ) -> str:
        """Log configuration change."""
        return self.log(
            event_type=AuditEventType.CONFIG_CHANGED,
            severity=AuditSeverity.WARNING,
            action="config_change",
            result="success",
            user_id=user_id,
            resource=config_key,
            details={
                "key": config_key,
                "old_value": str(old_value)[:500],
                "new_value": str(new_value)[:500]
            }
        )

    def get_event_count(self) -> int:
        """Get total events logged."""
        return self._event_count

    def query_events(
        self,
        start_time: float | None = None,
        end_time: float | None = None,
        user_id: str | None = None,
        event_type: AuditEventType | None = None,
        severity: AuditSeverity | None = None,
        limit: int = 100
    ) -> list[dict]:
        """Query audit events."""
        events = []

        # Search recent log files
        log_files = sorted(Path(self.log_dir).glob("audit_*.jsonl"), reverse=True)

        for log_file in log_files:
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            event = json.loads(line)

                            # Apply filters
                            if start_time and event.get("timestamp", 0) < start_time:
                                continue
                            if end_time and event.get("timestamp", 0) > end_time:
                                continue
                            if user_id and event.get("user_id") != user_id:
                                continue
                            if event_type and event.get("event_type") != event_type.value:
                                continue
                            if severity and event.get("severity") != severity.value:
                                continue

                            events.append(event)

                            if len(events) >= limit:
                                return events

                        except json.JSONDecodeError:
                            continue
            except Exception:
                continue

        return events


class AuditReporter:
    """Generate audit reports."""

    def __init__(self, logger: AuditLogger):
        self.logger = logger

    def generate_security_report(self, days: int = 7) -> dict:
        """Generate security report for the last N days."""
        end_time = time.time()
        start_time = end_time - (days * 86400)

        events = self.logger.query_events(
            start_time=start_time,
            end_time=end_time,
            limit=10000
        )

        # Count by type
        event_counts = {}
        failed_logins = 0
        rate_limits = 0
        permission_denied = 0
        unique_users = set()

        for event in events:
            event_type = event.get("event_type", "unknown")
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

            if event_type in ["login_failed", "LOGIN_FAILED"]:
                failed_logins += 1
            if event_type in ["rate_limit_exceeded", "RATE_LIMIT_EXCEEDED"]:
                rate_limits += 1
            if event_type in ["permission_denied", "PERMISSION_DENIED"]:
                permission_denied += 1
            if event.get("user_id"):
                unique_users.add(event["user_id"])

        return {
            "period_days": days,
            "total_events": len(events),
            "unique_users": len(unique_users),
            "event_breakdown": event_counts,
            "failed_logins": failed_logins,
            "rate_limit_exceeded": rate_limits,
            "permission_denied": permission_denied
        }

    def generate_user_activity_report(self, user_id: str, days: int = 30) -> dict:
        """Generate activity report for a specific user."""
        end_time = time.time()
        start_time = end_time - (days * 86400)

        events = self.logger.query_events(
            start_time=start_time,
            end_time=end_time,
            user_id=user_id,
            limit=1000
        )

        action_counts = {}
        for event in events:
            action = event.get("action", "unknown")
            action_counts[action] = action_counts.get(action, 0) + 1

        return {
            "user_id": user_id,
            "period_days": days,
            "total_actions": len(events),
            "action_breakdown": action_counts
        }


# Global audit logger instance
_audit_logger: AuditLogger | None = None


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def audit_log(
    event_type: AuditEventType,
    action: str,
    **kwargs
) -> str:
    """Convenience function for logging audit events."""
    return get_audit_logger().log(event_type, AuditSeverity.INFO, action, **kwargs)