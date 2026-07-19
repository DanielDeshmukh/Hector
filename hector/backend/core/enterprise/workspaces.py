"""
Team Workspace Management for HECTOR Enterprise.
Provides multi-tenant workspace support.
"""

from __future__ import annotations
import json
import time
import hashlib
import threading
from dataclasses import dataclass, field
import logging


@dataclass
class Workspace:
    """Represents a team workspace."""

    workspace_id: str
    name: str
    description: str | None
    created_at: float
    created_by: str
    is_active: bool = True
    settings: dict = field(default_factory=dict)
    member_count: int = 0
    storage_used_mb: float = 0.0


@dataclass
class WorkspaceMember:
    """Represents a workspace member."""

    user_id: str
    username: str
    workspace_id: str
    role: str  # admin, member, viewer
    joined_at: float
    permissions: list[str] = field(default_factory=list)


@dataclass
class WorkspaceAnalytics:
    """Workspace usage analytics."""

    workspace_id: str
    total_searches: int = 0
    total_documents: int = 0
    total_exports: int = 0
    storage_used_mb: float = 0.0
    active_members: int = 0
    last_activity: float | None = None


class WorkspaceManager:
    """Manages team workspaces."""

    def __init__(self, storage_path: str | None = None):
        self.storage_path = storage_path or self._get_default_storage_path()
        self._workspaces: dict[str, Workspace] = {}
        self._members: dict[str, list[WorkspaceMember]] = {}  # workspace_id -> members
        self._analytics: dict[str, WorkspaceAnalytics] = {}
        self._lock = threading.Lock()
        self._load_data()

    def _get_default_storage_path(self) -> str:
        """Get default storage path."""
        import os

        return os.path.join(os.path.dirname(__file__), "..", "..", "data", "enterprise")

    def _load_data(self) -> None:
        """Load workspaces from storage."""
        import os

        os.makedirs(self.storage_path, exist_ok=True)

        workspace_file = os.path.join(self.storage_path, "workspaces.json")
        if os.path.exists(workspace_file):
            try:
                with open(workspace_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                    for ws_data in data.get("workspaces", []):
                        workspace = Workspace(
                            workspace_id=ws_data["workspace_id"],
                            name=ws_data["name"],
                            description=ws_data.get("description"),
                            created_at=ws_data["created_at"],
                            created_by=ws_data["created_by"],
                            is_active=ws_data.get("is_active", True),
                            settings=ws_data.get("settings", {}),
                        )
                        self._workspaces[workspace.workspace_id] = workspace

                    # Load members
                    for ws_id, members_data in data.get("members", {}).items():
                        self._members[ws_id] = [
                            WorkspaceMember(
                                user_id=m["user_id"],
                                username=m["username"],
                                workspace_id=m["workspace_id"],
                                role=m["role"],
                                joined_at=m["joined_at"],
                                permissions=m.get("permissions", []),
                            )
                            for m in members_data
                        ]

                    # Load analytics
                    for an_data in data.get("analytics", {}):
                        self._analytics[an_data["workspace_id"]] = WorkspaceAnalytics(
                            workspace_id=an_data["workspace_id"],
                            total_searches=an_data.get("total_searches", 0),
                            total_documents=an_data.get("total_documents", 0),
                            total_exports=an_data.get("total_exports", 0),
                            storage_used_mb=an_data.get("storage_used_mb", 0.0),
                            active_members=an_data.get("active_members", 0),
                            last_activity=an_data.get("last_activity"),
                        )
            except Exception:
                logging.debug(
                    "Failed to load workspaces from %s", workspace_file, exc_info=True
                )

    def _save_data(self) -> None:
        """Save workspaces to storage."""
        import os

        os.makedirs(self.storage_path, exist_ok=True)

        workspace_file = os.path.join(self.storage_path, "workspaces.json")

        # Convert members to serializable format
        members_dict = {}
        for ws_id, members in self._members.items():
            members_dict[ws_id] = [
                {
                    "user_id": m.user_id,
                    "username": m.username,
                    "workspace_id": m.workspace_id,
                    "role": m.role,
                    "joined_at": m.joined_at,
                    "permissions": m.permissions,
                }
                for m in members
            ]

        # Convert analytics to serializable format
        analytics_list = [
            {
                "workspace_id": a.workspace_id,
                "total_searches": a.total_searches,
                "total_documents": a.total_documents,
                "total_exports": a.total_exports,
                "storage_used_mb": a.storage_used_mb,
                "active_members": a.active_members,
                "last_activity": a.last_activity,
            }
            for a in self._analytics.values()
        ]

        data = {
            "workspaces": [
                {
                    "workspace_id": w.workspace_id,
                    "name": w.name,
                    "description": w.description,
                    "created_at": w.created_at,
                    "created_by": w.created_by,
                    "is_active": w.is_active,
                    "settings": w.settings,
                }
                for w in self._workspaces.values()
            ],
            "members": members_dict,
            "analytics": analytics_list,
        }

        with open(workspace_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _generate_workspace_id(self) -> str:
        """Generate unique workspace ID."""
        return f"ws_{hashlib.sha256(str(time.time()).encode()).hexdigest()[:12]}"

    def create_workspace(
        self,
        name: str,
        created_by: str,
        description: str | None = None,
        settings: dict | None = None,
    ) -> Workspace:
        """Create a new workspace."""
        with self._lock:
            workspace = Workspace(
                workspace_id=self._generate_workspace_id(),
                name=name,
                description=description,
                created_at=time.time(),
                created_by=created_by,
                settings=settings or {},
            )
            self._workspaces[workspace.workspace_id] = workspace
            self._members[workspace.workspace_id] = []
            self._analytics[workspace.workspace_id] = WorkspaceAnalytics(
                workspace_id=workspace.workspace_id
            )
            self._save_data()

            return workspace

    def get_workspace(self, workspace_id: str) -> Workspace | None:
        """Get workspace by ID."""
        return self._workspaces.get(workspace_id)

    def update_workspace(self, workspace_id: str, **kwargs) -> Workspace | None:
        """Update workspace details."""
        with self._lock:
            workspace = self._workspaces.get(workspace_id)
            if not workspace:
                return None

            for key, value in kwargs.items():
                if hasattr(workspace, key):
                    setattr(workspace, key, value)

            self._save_data()
            return workspace

    def delete_workspace(self, workspace_id: str) -> bool:
        """Delete a workspace."""
        with self._lock:
            if workspace_id in self._workspaces:
                del self._workspaces[workspace_id]
                if workspace_id in self._members:
                    del self._members[workspace_id]
                if workspace_id in self._analytics:
                    del self._analytics[workspace_id]
                self._save_data()
                return True
            return False

    def add_member(
        self, workspace_id: str, user_id: str, username: str, role: str = "member"
    ) -> WorkspaceMember | None:
        """Add a member to workspace."""
        with self._lock:
            workspace = self._workspaces.get(workspace_id)
            if not workspace:
                return None

            member = WorkspaceMember(
                user_id=user_id,
                username=username,
                workspace_id=workspace_id,
                role=role,
                joined_at=time.time(),
            )

            if workspace_id not in self._members:
                self._members[workspace_id] = []

            self._members[workspace_id].append(member)
            workspace.member_count = len(self._members[workspace_id])

            # Update analytics
            if workspace_id in self._analytics:
                self._analytics[workspace_id].active_members = workspace.member_count

            self._save_data()
            return member

    def remove_member(self, workspace_id: str, user_id: str) -> bool:
        """Remove a member from workspace."""
        with self._lock:
            if workspace_id not in self._members:
                return False

            members = self._members[workspace_id]
            self._members[workspace_id] = [m for m in members if m.user_id != user_id]

            # Update counts
            workspace = self._workspaces.get(workspace_id)
            if workspace:
                workspace.member_count = len(self._members[workspace_id])

            if workspace_id in self._analytics:
                self._analytics[workspace_id].active_members = workspace.member_count

            self._save_data()
            return True

    def get_members(self, workspace_id: str) -> list[WorkspaceMember]:
        """Get all members of a workspace."""
        return self._members.get(workspace_id, [])

    def get_user_workspaces(self, user_id: str) -> list[Workspace]:
        """Get all workspaces a user belongs to."""
        workspaces = []
        for ws_id, members in self._members.items():
            if any(m.user_id == user_id for m in members):
                workspace = self._workspaces.get(ws_id)
                if workspace:
                    workspaces.append(workspace)
        return workspaces

    def update_analytics(
        self,
        workspace_id: str,
        search: bool = False,
        document: bool = False,
        export: bool = False,
    ) -> None:
        """Update workspace analytics."""
        with self._lock:
            if workspace_id not in self._analytics:
                return

            analytics = self._analytics[workspace_id]

            if search:
                analytics.total_searches += 1
            if document:
                analytics.total_documents += 1
            if export:
                analytics.total_exports += 1

            analytics.last_activity = time.time()

    def get_analytics(self, workspace_id: str) -> WorkspaceAnalytics | None:
        """Get workspace analytics."""
        return self._analytics.get(workspace_id)

    def list_workspaces(self, include_inactive: bool = False) -> list[Workspace]:
        """List all workspaces."""
        workspaces = list(self._workspaces.values())
        if not include_inactive:
            workspaces = [w for w in workspaces if w.is_active]
        return workspaces


# Global workspace manager instance
_workspace_manager: WorkspaceManager | None = None


def get_workspace_manager() -> WorkspaceManager:
    """Get the global workspace manager."""
    global _workspace_manager
    if _workspace_manager is None:
        _workspace_manager = WorkspaceManager()
    return _workspace_manager


def create_workspace(name: str, created_by: str, **kwargs) -> Workspace:
    """Convenience function to create workspace."""
    return get_workspace_manager().create_workspace(name, created_by, **kwargs)


def get_user_workspaces(user_id: str) -> list[Workspace]:
    """Convenience function to get user workspaces."""
    return get_workspace_manager().get_user_workspaces(user_id)
