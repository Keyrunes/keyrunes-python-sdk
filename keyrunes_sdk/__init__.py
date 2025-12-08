"""Keyrunes SDK - Python client for Keyrunes Authorization System."""

__version__ = "0.1.0"

from keyrunes_sdk.client import KeyrunesClient
from keyrunes_sdk.decorators import require_group, require_admin
from keyrunes_sdk.config import (
    configure,
    get_global_client,
    clear_global_client,
    get_config,
)
from keyrunes_sdk.exceptions import (
    KeyrunesError,
    AuthenticationError,
    AuthorizationError,
    GroupNotFoundError,
    UserNotFoundError,
    NetworkError,
)
from keyrunes_sdk.models import (
    User,
    Group,
    Token,
    UserRegistration,
    AdminRegistration,
    LoginCredentials,
    GroupCheck,
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
