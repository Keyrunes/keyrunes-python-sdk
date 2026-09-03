"""Data models for Keyrunes SDK."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field


class User(BaseModel):
    """User model."""

    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: EmailStr = Field(..., description="User email")
    groups: List[str] = Field(
        default_factory=list, description="List of group IDs"
    )
    attributes: Dict[str, Any] = Field(
        default_factory=dict, description="User attributes"
    )
    created_at: Optional[datetime] = Field(
        None, description="Creation timestamp"
    )
    updated_at: Optional[datetime] = Field(
        None, description="Last update timestamp"
    )
    is_active: bool = Field(True, description="Whether user is active")
    is_admin: bool = Field(
        False, description="Whether user has admin privileges"
    )
    # Keyrunes answers with two identifiers: ``id`` is the external UUID and
    # ``user_id`` is the internal integer the JWT carries as ``sub``. ``id``
    # above keeps its historical precedence; this field is kept alongside it so
    # a caller that keys its own records off ``sub`` can reach that value
    # without re-parsing the token.
    user_id: Optional[str] = Field(
        None, description="Internal user identifier, as carried by the JWT sub"
    )
    namespace: Optional[str] = Field(
        None, description="Namespace (tenant) the user belongs to"
    )
    organization_id: Optional[Any] = Field(
        None, description="Organization the user belongs to"
    )
    first_login: bool = Field(
        False, description="Whether the user has yet to complete a first login"
    )


class Group(BaseModel):
    """Group model."""

    id: str = Field(..., description="Group ID")
    name: str = Field(..., description="Group name")
    description: Optional[str] = Field(None, description="Group description")
    permissions: List[str] = Field(
        default_factory=list, description="List of permissions"
    )
    created_at: Optional[datetime] = Field(
        None, description="Creation timestamp"
    )


class Token(BaseModel):
    """Authentication token model."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: Optional[int] = Field(
        None, description="Token expiration in seconds"
    )
    refresh_token: Optional[str] = Field(None, description="Refresh token")
    user: Optional[User] = Field(None, description="User information")
    requires_password_change: bool = Field(
        False,
        description="Whether the server wants the password changed before use",
    )


class UserRegistration(BaseModel):
    """User registration data."""

    username: str = Field(
        ..., min_length=3, max_length=50, description="Username"
    )
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=8, description="Password")
    namespace: str = Field("default", description="User namespace")
    attributes: Dict[str, Any] = Field(
        default_factory=dict, description="Additional attributes"
    )


class AdminRegistration(UserRegistration):
    """Admin registration data (extends UserRegistration)."""

    admin_key: str = Field(..., description="Admin registration key")


class LoginCredentials(BaseModel):
    """Login credentials."""

    identity: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")
    namespace: str = Field("default", description="User namespace")

    @classmethod
    def from_username(
        cls, username: str, password: str, namespace: str = "default"
    ) -> "LoginCredentials":
        """Create from username parameter (for backward compatibility)."""
        return cls(identity=username, password=password, namespace=namespace)


class GroupCheck(BaseModel):
    """Group membership check result."""

    user_id: str = Field(..., description="User ID")
    group_id: str = Field(..., description="Group ID")
    has_access: bool = Field(
        ..., description="Whether user has access to group"
    )
    checked_at: datetime = Field(
        default_factory=datetime.utcnow, description="Check timestamp"
    )
