"""Custom exceptions for Keyrunes SDK."""


class KeyrunesError(Exception):
    """Base exception for all Keyrunes SDK errors."""

    pass


class AuthenticationError(KeyrunesError):
    """Raised when authentication fails."""

    pass


class AuthorizationError(KeyrunesError):
    """Raised when authorization fails."""

    pass


class GroupNotFoundError(KeyrunesError):
    """Raised when a group is not found."""

    pass


class UserNotFoundError(KeyrunesError):
    """Raised when a user is not found."""

    pass


class InvalidTokenError(KeyrunesError):
    """Raised when token is invalid or expired."""

    pass


class NetworkError(KeyrunesError):
    """Raised when network request fails."""

    pass
