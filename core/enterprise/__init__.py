"""
HECTOR Enterprise Module.
Provides enterprise features: users, roles, workspaces, audit, rate limiting.
"""

from core.enterprise.validators import (
    InputSanitizer,
    InputValidator,
    ValidationError,
    validate_json_payload,
    generate_secure_token,
    hash_sensitive_data,
    DataSanitizer,
)

from core.enterprise.rate_limiter import (
    RateLimitConfig,
    TokenBucket,
    SlidingWindowRateLimiter,
    RateLimitManager,
    IPRateLimiter,
    APIClientRateLimiter,
    get_rate_limit_manager,
    check_rate_limit,
)

from core.enterprise.audit import (
    AuditEventType,
    AuditSeverity,
    AuditEvent,
    AuditLogger,
    AuditReporter,
    get_audit_logger,
    audit_log,
)

from core.enterprise.users import (
    UserRole,
    Permission,
    User,
    APIKey,
    UserManager,
    PermissionChecker,
    get_user_manager,
    get_permission_checker,
    check_permission,
)

from core.enterprise.workspaces import (
    Workspace,
    WorkspaceMember,
    WorkspaceAnalytics,
    WorkspaceManager,
    get_workspace_manager,
    create_workspace,
    get_user_workspaces,
)

__all__ = [
    # Validators
    "InputSanitizer",
    "InputValidator",
    "ValidationError",
    "validate_json_payload",
    "generate_secure_token",
    "hash_sensitive_data",
    "DataSanitizer",
    # Rate Limiter
    "RateLimitConfig",
    "TokenBucket",
    "SlidingWindowRateLimiter",
    "RateLimitManager",
    "IPRateLimiter",
    "APIClientRateLimiter",
    "get_rate_limit_manager",
    "check_rate_limit",
    # Audit
    "AuditEventType",
    "AuditSeverity",
    "AuditEvent",
    "AuditLogger",
    "AuditReporter",
    "get_audit_logger",
    "audit_log",
    # Users
    "UserRole",
    "Permission",
    "User",
    "APIKey",
    "UserManager",
    "PermissionChecker",
    "get_user_manager",
    "get_permission_checker",
    "check_permission",
    # Workspaces
    "Workspace",
    "WorkspaceMember",
    "WorkspaceAnalytics",
    "WorkspaceManager",
    "get_workspace_manager",
    "create_workspace",
    "get_user_workspaces",
]

__version__ = "2.1.0"