"""Keyrunes SDK - Python client for Keyrunes Authorization System."""

__version__ = "0.1.0"

from keyrunes_sdk.client import KeyrunesClient
from keyrunes_sdk.config import (
    clear_global_client,
    configure,
    get_config,
    get_global_client,
)
from keyrunes_sdk.decorators import require_admin, require_group
from keyrunes_sdk.exceptions import (
    AuthenticationError,
    AuthorizationError,
    GroupNotFoundError,
    KeyrunesError,
    NetworkError,
    UserNotFoundError,
)
from keyrunes_sdk.models import (
    AdminRegistration,
    Group,
    GroupCheck,
    LoginCredentials,
    Token,
    User,
    UserRegistration,
)

__all__ = [
    "KeyrunesClient",
    "configure",
    "get_global_client",
    "clear_global_client",
    "get_config",
    "require_group",
    "require_admin",
    "KeyrunesError",
    "AuthenticationError",
    "AuthorizationError",
    "GroupNotFoundError",
    "UserNotFoundError",
    "NetworkError",
    "User",
    "Group",
    "Token",
    "UserRegistration",
    "AdminRegistration",
    "LoginCredentials",
    "GroupCheck",
]
