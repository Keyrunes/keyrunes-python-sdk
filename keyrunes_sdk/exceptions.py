"""Custom exceptions for Keyrunes SDK."""

from typing import Optional


class KeyrunesError(Exception):
    """Base exception for all Keyrunes SDK errors.

    Args:
        message: Human-readable description.
        status_code: HTTP status the server answered with, when the error came
            from a response rather than from the transport. Callers use it to
            tell "the server refused this request" (4xx, the caller's problem)
            from "the server or the network failed" (5xx or no response at
            all), which otherwise look identical.
    """

    def __init__(
        self, message: str = "", status_code: Optional[int] = None
    ) -> None:
        super().__init__(message)
        self.status_code = status_code


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
    """Raised when a request fails.

    ``status_code`` is set when the server answered and the response was an
    error; it is ``None`` when the request never got a response.
    """

    pass
