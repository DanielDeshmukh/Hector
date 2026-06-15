"""
User Management and Roles for HECTOR Enterprise.
Provides multi-user support with role-based access control.
"""

from __future__ import annotations
import json
import time
import hashlib
import secrets

import bcrypt
import threading
from dataclasses import dataclass, field
import logging
from typing import Any, Callable
from enum import Enum


class UserRole(Enum):
    """User roles in the system."""
    ADMIN = "admin"           # Full system access
    RESEARCHER = "researcher" # Search, ingest, analyze
    VIEWER = "viewer"         # Read-only access
    API_CLIENT = "api_client" # Programmatic access


class Permission(Enum):
    """System permissions."""
    # Search
    SEARCH = "search"
    ADVANCED_SEARCH = "advanced_search"

    # Document
    UPLOAD_DOCUMENT = "upload_document"
    DELETE_DOCUMENT = "delete_document"
    EXPORT_DOCUMENT = "export_document"

    # User Management
    CREATE_USER = "create_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"

    # System
    VIEW_AUDIT_LOGS = "view_audit_logs"
    MANAGE_CONFIG = "manage_config"
    VIEW_ANALYTICS = "view_analytics"

    # API
    API_ACCESS = "api_access"
    CREATE_API_KEY = "create_api_key"


# Role to Permission mapping
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        Permission.SEARCH,
        Permission.ADVANCED_SEARCH,
        Permission.UPLOAD_DOCUMENT,
        Permission.DELETE_DOCUMENT,
        Permission.EXPORT_DOCUMENT,
        Permission.CREATE_USER,
        Permission.UPDATE_USER,
        Permission.DELETE_USER,
        Permission.VIEW_AUDIT_LOGS,
        Permission.MANAGE_CONFIG,
        Permission.VIEW_ANALYTICS,
        Permission.API_ACCESS,
        Permission.CREATE_API_KEY,
    ],
    UserRole.RESEARCHER: [
        Permission.SEARCH,
        Permission.ADVANCED_SEARCH,
        Permission.UPLOAD_DOCUMENT,
        Permission.EXPORT_DOCUMENT,
        Permission.VIEW_ANALYTICS,
    ],
    UserRole.VIEWER: [
        Permission.SEARCH,
    ],
    UserRole.API_CLIENT: [
        Permission.SEARCH,
        Permission.API_ACCESS,
    ],
}


@dataclass
class User:
    """Represents a user in the system."""
    user_id: str
    username: str
    email: str
    role: UserRole
    created_at: float
    last_login: float | None = None
    is_active: bool = True
    workspace_id: str | None = None
    metadata: dict = field(default_factory=dict)

    def has_permission(self, permission: Permission) -> bool:
        """Check if user has a specific permission."""
        if not self.is_active:
            return False
        return permission in ROLE_PERMISSIONS.get(self.role, [])

    def to_dict(self) -> dict:
        """Convert to dictionary (without sensitive data)."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "role": self.role.value,
            "created_at": self.created_at,
            "last_login": self.last_login,
            "is_active": self.is_active,
            "workspace_id": self.workspace_id,
            "metadata": self.metadata
        }


@dataclass
class APIKey:
    """Represents an API key."""
    key_id: str
    client_id: str
    key_hash: str
    name: str
    created_at: float
    expires_at: float | None = None
    last_used: float | None = None
    is_active: bool = True
    rate_limit: int = 60  # requests per minute


class UserManager:
    """Manages users and authentication."""

    def __init__(self, storage_path: str | None = None):
        self.storage_path = storage_path or self._get_default_storage_path()
        self._users: dict[str, User] = {}
        self._api_keys: dict[str, APIKey] = {}
        self._lock = threading.Lock()
        self._load_users()

    def _get_default_storage_path(self) -> str:
        """Get default storage path."""
        import os
        return os.path.join(
            os.path.dirname(__file__), "..", "..", "data", "enterprise"
        )

    def _load_users(self) -> None:
        """Load users from storage."""
        import os
        os.makedirs(self.storage_path, exist_ok=True)

        user_file = os.path.join(self.storage_path, "users.json")
        if os.path.exists(user_file):
            try:
                with open(user_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for user_data in data.get("users", []):
                        user = User(
                            user_id=user_data["user_id"],
                            username=user_data["username"],
                            email=user_data["email"],
                            role=UserRole(user_data["role"]),
                            created_at=user_data["created_at"],
                            last_login=user_data.get("last_login"),
                            is_active=user_data.get("is_active", True),
                            workspace_id=user_data.get("workspace_id"),
                            metadata=user_data.get("metadata", {})
                        )
                        self._users[user.user_id] = user
            except Exception:
                logging.debug("Failed to load users from %s", user_file, exc_info=True)

    def _save_users(self) -> None:
        """Save users to storage."""
        import os
        os.makedirs(self.storage_path, exist_ok=True)

        user_file = os.path.join(self.storage_path, "users.json")
        with open(user_file, "w", encoding="utf-8") as f:
            data = {
                "users": [
                    {
                        "user_id": u.user_id,
                        "username": u.username,
                        "email": u.email,
                        "role": u.role.value,
                        "created_at": u.created_at,
                        "last_login": u.last_login,
                        "is_active": u.is_active,
                        "workspace_id": u.workspace_id,
                        "metadata": u.metadata
                    }
                    for u in self._users.values()
                ]
            }
            json.dump(data, f, indent=2)

    def _generate_user_id(self) -> str:
        """Generate unique user ID."""
        return hashlib.sha256(
            f"{time.time()}{secrets.token_hex(8)}".encode()
        ).hexdigest()[:16]

    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        role: UserRole = UserRole.VIEWER,
        workspace_id: str | None = None
    ) -> User:
        """Create a new user."""
        with self._lock:
            # Check if username or email already exists
            for user in self._users.values():
                if user.username == username:
                    raise ValueError("Username already exists")
                if user.email == email:
                    raise ValueError("Email already exists")

            # Validate password
            if len(password) < 8:
                raise ValueError("Password must be at least 8 characters")

            # Create user
            user = User(
                user_id=self._generate_user_id(),
                username=username,
                email=email,
                role=role,
                created_at=time.time(),
                workspace_id=workspace_id,
                metadata={"password_hash": bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()}
            )
            self._users[user.user_id] = user
            self._save_users()

            return user

    def authenticate(self, username: str, password: str) -> User | None:
        """Authenticate a user with password verification."""
        for user in self._users.values():
            if user.username == username and user.is_active:
                stored_hash = user.metadata.get("password_hash", "")
                if stored_hash and bcrypt.checkpw(password.encode(), stored_hash.encode()):
                    user.last_login = time.time()
                    self._save_users()
                    return user
                return None

        return None

    def get_user(self, user_id: str) -> User | None:
        """Get user by ID."""
        return self._users.get(user_id)

    def get_user_by_username(self, username: str) -> User | None:
        """Get user by username."""
        for user in self._users.values():
            if user.username == username:
                return user
        return None

    def update_user(self, user_id: str, **kwargs) -> User | None:
        """Update user details."""
        with self._lock:
            user = self._users.get(user_id)
            if not user:
                return None

            for key, value in kwargs.items():
                if key == "role" and isinstance(value, str):
                    value = UserRole(value)
                if key == "email" and value != user.email:
                    # Check uniqueness
                    for u in self._users.values():
                        if u.email == value and u.user_id != user_id:
                            raise ValueError("Email already exists")
                if hasattr(user, key):
                    setattr(user, key, value)

            self._save_users()
            return user

    def delete_user(self, user_id: str) -> bool:
        """Delete a user."""
        with self._lock:
            if user_id in self._users:
                del self._users[user_id]
                self._save_users()
                return True
            return False

    def list_users(self, role: UserRole | None = None) -> list[User]:
        """List all users, optionally filtered by role."""
        users = list(self._users.values())
        if role:
            users = [u for u in users if u.role == role]
        return users

    def create_api_key(
        self,
        client_id: str,
        name: str,
        rate_limit: int = 60
    ) -> APIKey:
        """Create a new API key."""
        with self._lock:
            key = secrets.token_urlsafe(32)
            key_hash = hashlib.sha256(key.encode()).hexdigest()

            api_key = APIKey(
                key_id=secrets.token_hex(8),
                client_id=client_id,
                key_hash=key_hash,
                name=name,
                created_at=time.time(),
                rate_limit=rate_limit
            )

            self._api_keys[api_key.key_id] = api_key
            return api_key, key  # Return key only once!

    def validate_api_key(self, key: str) -> tuple[bool, APIKey | None]:
        """Validate an API key."""
        key_hash = hashlib.sha256(key.encode()).hexdigest()

        for api_key in self._api_keys.values():
            if api_key.key_hash == key_hash and api_key.is_active:
                # Check expiration
                if api_key.expires_at and time.time() > api_key.expires_at:
                    return False, None
                api_key.last_used = time.time()
                return True, api_key

        return False, None

    def revoke_api_key(self, key_id: str) -> bool:
        """Revoke an API key."""
        with self._lock:
            if key_id in self._api_keys:
                self._api_keys[key_id].is_active = False
                return True
            return False


class PermissionChecker:
    """Checks permissions for users and API keys."""

    def __init__(self, user_manager: UserManager):
        self.user_manager = user_manager

    def check_permission(
        self,
        user_id: str | None,
        permission: Permission,
        api_key: str | None = None
    ) -> tuple[bool, str | None]:
        """Check if user has permission."""
        # If API key provided, check via API key
        if api_key:
            valid, api_key_obj = self.user_manager.validate_api_key(api_key)
            if not api_key_obj:
                return False, "Invalid API key"
            # API clients have limited permissions
            if permission == Permission.SEARCH:
                return True, api_key_obj.client_id
            return False, "Insufficient permissions"

        # Check user permissions
        if not user_id:
            return False, "No user identified"

        user = self.user_manager.get_user(user_id)
        if not user:
            return False, "User not found"

        if not user.is_active:
            return False, "User account is disabled"

        if not user.has_permission(permission):
            return False, f"Missing required permission: {permission.value}"

        return True, user_id


# Global user manager instance
_user_manager: UserManager | None = None


def get_user_manager() -> UserManager:
    """Get the global user manager."""
    global _user_manager
    if _user_manager is None:
        _user_manager = UserManager()
    return _user_manager


def get_permission_checker() -> PermissionChecker:
    """Get the global permission checker."""
    return PermissionChecker(get_user_manager())


def check_permission(
    user_id: str | None,
    permission: Permission,
    api_key: str | None = None
) -> tuple[bool, str | None]:
    """Convenience function to check permissions."""
    return get_permission_checker().check_permission(user_id, permission, api_key)