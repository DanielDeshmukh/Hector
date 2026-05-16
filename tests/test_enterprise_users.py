"""
Unit tests for Enterprise Users and Roles Module.
Tests user management, authentication, and permissions.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.enterprise.users import (
    UserRole,
    Permission,
    User,
    APIKey,
    UserManager,
    PermissionChecker,
    get_user_manager,
    check_permission,
    ROLE_PERMISSIONS,
)


class TestUserRole:
    """Test user role enum."""

    def test_role_values(self):
        """Test role enum values."""
        assert UserRole.ADMIN.value == "admin"
        assert UserRole.RESEARCHER.value == "researcher"
        assert UserRole.VIEWER.value == "viewer"
        assert UserRole.API_CLIENT.value == "api_client"


class TestPermission:
    """Test permission enum."""

    def test_permission_values(self):
        """Test permission enum values."""
        assert Permission.SEARCH.value == "search"
        assert Permission.CREATE_USER.value == "create_user"
        assert Permission.VIEW_AUDIT_LOGS.value == "view_audit_logs"


class TestRolePermissions:
    """Test role-permission mapping."""

    def test_admin_has_all_permissions(self):
        """Test admin has all permissions."""
        perms = ROLE_PERMISSIONS[UserRole.ADMIN]
        assert Permission.SEARCH in perms
        assert Permission.CREATE_USER in perms
        assert Permission.DELETE_USER in perms
        assert Permission.VIEW_AUDIT_LOGS in perms

    def test_researcher_limited_permissions(self):
        """Test researcher has limited permissions."""
        perms = ROLE_PERMISSIONS[UserRole.RESEARCHER]
        assert Permission.SEARCH in perms
        assert Permission.CREATE_USER not in perms
        assert Permission.DELETE_USER not in perms

    def test_viewer_minimal_permissions(self):
        """Test viewer has minimal permissions."""
        perms = ROLE_PERMISSIONS[UserRole.VIEWER]
        assert perms == [Permission.SEARCH]

    def test_api_client_permissions(self):
        """Test API client permissions."""
        perms = ROLE_PERMISSIONS[UserRole.API_CLIENT]
        assert Permission.SEARCH in perms
        assert Permission.API_ACCESS in perms


class TestUser:
    """Test user dataclass."""

    def test_user_creation(self):
        """Test user creation."""
        user = User(
            user_id="user123",
            username="testuser",
            email="test@example.com",
            role=UserRole.VIEWER,
            created_at=1234567890.0
        )
        assert user.user_id == "user123"
        assert user.username == "testuser"
        assert user.role == UserRole.VIEWER
        assert user.is_active is True

    def test_user_has_permission_true(self):
        """Test user has permission."""
        user = User(
            user_id="user123",
            username="testuser",
            email="test@example.com",
            role=UserRole.ADMIN,
            created_at=1234567890.0
        )
        assert user.has_permission(Permission.SEARCH) is True

    def test_user_has_permission_false(self):
        """Test user lacks permission."""
        user = User(
            user_id="user123",
            username="testuser",
            email="test@example.com",
            role=UserRole.VIEWER,
            created_at=1234567890.0
        )
        assert user.has_permission(Permission.CREATE_USER) is False

    def test_user_inactive_no_permissions(self):
        """Test inactive user has no permissions."""
        user = User(
            user_id="user123",
            username="testuser",
            email="test@example.com",
            role=UserRole.ADMIN,
            created_at=1234567890.0,
            is_active=False
        )
        assert user.has_permission(Permission.SEARCH) is False


class TestUserManager:
    """Test user manager."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create user manager with temp storage."""
        return UserManager(storage_path=str(tmp_path))

    def test_manager_initialization(self, manager):
        """Test manager initializes."""
        assert manager is not None
        assert isinstance(manager._users, dict)

    def test_create_user(self, manager):
        """Test user creation."""
        user = manager.create_user(
            username="testuser",
            email="test@example.com",
            password="Password123",
            role=UserRole.VIEWER
        )
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == UserRole.VIEWER

    def test_create_user_duplicate_username(self, manager):
        """Test duplicate username rejection."""
        manager.create_user("user1", "user1@test.com", "Password123")
        with pytest.raises(ValueError):
            manager.create_user("user1", "user2@test.com", "Password123")

    def test_create_user_duplicate_email(self, manager):
        """Test duplicate email rejection."""
        manager.create_user("user1", "same@test.com", "Password123")
        with pytest.raises(ValueError):
            manager.create_user("user2", "same@test.com", "Password123")

    def test_create_user_password_too_short(self, manager):
        """Test password too short rejection."""
        with pytest.raises(ValueError):
            manager.create_user("user", "test@test.com", "short")

    def test_authenticate_success(self, manager):
        """Test successful authentication."""
        manager.create_user("testuser", "test@example.com", "Password123")
        user = manager.authenticate("testuser", "Password123")
        assert user is not None

    def test_authenticate_failure(self, manager):
        """Test authentication failure."""
        user = manager.authenticate("nonexistent", "Password123")
        assert user is None

    def test_get_user(self, manager):
        """Test get user by ID."""
        created = manager.create_user("user", "user@test.com", "Password123")
        retrieved = manager.get_user(created.user_id)
        assert retrieved is not None
        assert retrieved.username == "user"

    def test_get_user_by_username(self, manager):
        """Test get user by username."""
        manager.create_user("testuser", "test@test.com", "Password123")
        user = manager.get_user_by_username("testuser")
        assert user is not None

    def test_update_user(self, manager):
        """Test user update."""
        user = manager.create_user("user", "user@test.com", "Password123")
        updated = manager.update_user(user.user_id, role=UserRole.ADMIN)
        assert updated.role == UserRole.ADMIN

    def test_delete_user(self, manager):
        """Test user deletion."""
        user = manager.create_user("user", "user@test.com", "Password123")
        result = manager.delete_user(user.user_id)
        assert result is True
        assert manager.get_user(user.user_id) is None

    def test_list_users(self, manager):
        """Test listing users."""
        manager.create_user("user1", "user1@test.com", "Password123")
        manager.create_user("user2", "user2@test.com", "Password123")
        users = manager.list_users()
        assert len(users) >= 2

    def test_list_users_filtered_by_role(self, manager):
        """Test listing users by role."""
        manager.create_user("user1", "user1@test.com", "Password123", UserRole.VIEWER)
        manager.create_user("user2", "user2@test.com", "Password123", UserRole.ADMIN)
        viewers = manager.list_users(role=UserRole.VIEWER)
        assert len(viewers) >= 1


class TestAPIKey:
    """Test API key functionality."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create user manager."""
        return UserManager(storage_path=str(tmp_path))

    def test_create_api_key(self, manager):
        """Test API key creation."""
        api_key, key = manager.create_api_key("client1", "Test Key")
        assert api_key is not None
        assert key is not None
        assert len(key) >= 32

    def test_validate_api_key(self, manager):
        """Test API key validation."""
        api_key, key = manager.create_api_key("client1", "Test Key")
        valid, validated = manager.validate_api_key(key)
        assert valid is True
        assert validated is not None

    def test_validate_invalid_api_key(self, manager):
        """Test invalid API key validation."""
        valid, validated = manager.validate_api_key("invalid_key_123")
        assert valid is False

    def test_revoke_api_key(self, manager):
        """Test API key revocation."""
        api_key, key = manager.create_api_key("client1", "Test Key")
        result = manager.revoke_api_key(api_key.key_id)
        assert result is True
        valid, _ = manager.validate_api_key(key)
        assert valid is False


class TestPermissionChecker:
    """Test permission checker."""

    @pytest.fixture
    def checker(self, tmp_path):
        """Create permission checker."""
        return PermissionChecker(UserManager(storage_path=str(tmp_path)))

    def test_check_permission_granted(self, checker):
        """Test permission granted."""
        checker.user_manager.create_user("admin", "admin@test.com", "Password123", UserRole.ADMIN)
        allowed, _ = checker.check_permission("admin", Permission.SEARCH)
        assert allowed is True

    def test_check_permission_denied(self, checker):
        """Test permission denied."""
        checker.user_manager.create_user("viewer", "viewer@test.com", "Password123", UserRole.VIEWER)
        allowed, _ = checker.check_permission("viewer", Permission.CREATE_USER)
        assert allowed is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])