"""Keyrunes API Client."""

import os
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx
import jwt

from keyrunes_sdk.exceptions import (
    AuthenticationError,
    AuthorizationError,
    GroupNotFoundError,
    InvalidTokenError,
    NetworkError,
    UserNotFoundError,
)
from keyrunes_sdk.models import (
    AdminRegistration,
    GroupCheck,
    LoginCredentials,
    Token,
    User,
    UserRegistration,
)

#: Where the server answers "who is this token". The Keyrunes router exposes
#: this as ``/api/me``; there is no ``/api/users/me``.
#: Creates a user; answers with the bare user object.
ENDPOINT_REGISTER = "/api/register"

#: Where the server answers "who is this token".
ENDPOINT_ME = "/api/me"

#: Exchanges a still-valid token for a fresh one.
ENDPOINT_REFRESH_TOKEN = "/api/refresh-token"

#: Changes the password of whoever the bearer token identifies.
#:
#: ``/api/user/change-password``, and not ``/api/change-password``: the router
#: registers the first, and the handler behind the second is dead code marked
#: ``#[allow(dead_code)]``. Pointing at it answers 404.
ENDPOINT_CHANGE_PASSWORD = "/api/user/change-password"


class KeyrunesClient:
    """
    Client for interacting with Keyrunes Authorization System.

    This client provides methods for:
    - User authentication (login)
    - User registration
    - Admin registration
    - Group membership verification
    - Authorization checks

    Args:
        base_url: Base URL of the Keyrunes API
            (e.g., "https://keyrunes.example.com")
        api_key: Optional API key for authentication
        organization_key: Optional Organization Key (required for v0.2.0+)
            If not provided, looks for KEYRUNES_ORG_KEY env var
        timeout: Request timeout in seconds (default: 30)

    Example:
        >>> client = KeyrunesClient("https://keyrunes.example.com")
        >>> token = client.login("user@example.com", "password123")
        >>> print(token.access_token)
    """

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        organization_key: Optional[str] = None,
        timeout: int = 30,
    ) -> None:
        """Initialize Keyrunes client."""
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        # Prioritize explicit argument, then env var
        self.organization_key = organization_key or os.getenv(
            "KEYRUNES_ORG_KEY"
        )
        self.timeout = timeout
        self._token: Optional[str] = None
        self._token_data: Optional[Dict[str, Any]] = None
        self._client = httpx.Client(timeout=timeout)

        if api_key:
            self._client.headers.update({"X-API-Key": api_key})

        if self.organization_key:
            self._client.headers.update(
                {"X-Organization-Key": self.organization_key}
            )

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        use_auth: bool = True,
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Keyrunes API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            data: Request body data
            params: Query parameters
            use_auth: Whether to include authentication header

        Returns:
            Response JSON data

        Raises:
            NetworkError: If request fails
            AuthenticationError: If authentication fails (401)
            AuthorizationError: If authorization fails (403)
        """
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))
        headers = {}

        if use_auth and self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        try:
            response = self._client.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=headers,
            )

            if response.status_code == 401:
                raise AuthenticationError(
                    "Authentication failed. Invalid credentials or token."
                )
            elif response.status_code == 403:
                raise AuthorizationError(
                    "Authorization denied. Insufficient permissions."
                )
            elif response.status_code == 404:
                raise UserNotFoundError("Resource not found.")
            elif response.status_code >= 400:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", response.text)
                except (ValueError, TypeError):
                    error_msg = (
                        response.text or f"HTTP {response.status_code} error"
                    )
                raise NetworkError(
                    f"Request failed: {error_msg}",
                    status_code=response.status_code,
                )

            try:
                result: Dict[str, Any] = response.json()
            except (ValueError, TypeError) as e:
                raise NetworkError(
                    f"Malformed JSON in response from {url}: {str(e)}"
                )
            return result

        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    @staticmethod
    def _normalize_user(data: Dict[str, Any]) -> User:
        """Convert API user payload to SDK User model."""
        if not data:
            raise NetworkError("Empty user payload received from server.")

        normalized: Dict[str, Any] = {}
        normalized["id"] = str(
            data.get("id") or data.get("user_id") or data.get("external_id")
        )
        normalized["username"] = data.get("username", "")
        normalized["email"] = data.get("email", "")
        normalized["groups"] = data.get("groups", []) or []
        normalized["attributes"] = data.get("attributes", {})
        normalized["is_active"] = data.get("is_active", True)
        groups = normalized["groups"]
        is_admin_flag = data.get("is_admin", False)
        has_admin_group = "admins" in groups or "superadmin" in groups
        has_admin_in_name = any("admin" in str(g).lower() for g in groups)
        normalized["is_admin"] = (
            is_admin_flag or has_admin_group or has_admin_in_name
        )
        # Carried through untouched so a caller can key its own records off the
        # same identifier the JWT ``sub`` uses, rather than off ``id``.
        raw_user_id = data.get("user_id")
        normalized["user_id"] = (
            str(raw_user_id) if raw_user_id is not None else None
        )
        normalized["namespace"] = data.get("namespace")
        normalized["organization_id"] = data.get("organization_id")
        normalized["first_login"] = bool(data.get("first_login", False))
        return User(**normalized)

    def _user_from_token_claims(self) -> User:
        """Build a :class:`User` out of the claims carried by the JWT.

        Only called once ``self._token_data`` is known to be populated.
        """
        token_data = self._token_data or {}
        return self._normalize_user(
            {
                "id": str(token_data.get("sub", "")),
                "username": token_data.get("username", ""),
                "email": token_data.get("email", ""),
                "groups": token_data.get("groups", []),
            }
        )

    def _parse_token_response(self, payload: Dict[str, Any]) -> Token:
        """
        Accept both legacy and current API token responses.

        - New API: {"token": "...", "user": {...},
          "requires_password_change": false}
        - Legacy: {access_token, token_type, expires_in,
          refresh_token, user}
        """
        if "access_token" in payload:
            user = payload.get("user")
            if isinstance(user, dict):
                payload["user"] = self._normalize_user(user)
            return Token(**payload)

        token_value = payload.get("token")
        if not token_value:
            raise AuthenticationError(
                "No token returned by authentication endpoint."
            )

        user_payload = payload.get("user")
        user_model = (
            self._normalize_user(user_payload)
            if isinstance(user_payload, dict)
            else None
        )

        return Token(
            access_token=token_value,
            token_type="bearer",
            expires_in=payload.get("expires_in"),
            refresh_token=payload.get("refresh_token"),
            user=user_model,
            requires_password_change=bool(
                payload.get("requires_password_change", False)
            ),
        )

    def login(
        self, username: str, password: str, namespace: str = "public"
    ) -> Token:
        """
        Authenticate user and obtain access token.

        Args:
            username: Username or email
            password: User password
            namespace: User namespace (default: "public")

        Returns:
            Token object containing access token and user info

        Raises:
            AuthenticationError: If login fails

        Example:
            >>> client = KeyrunesClient("https://keyrunes.example.com")
            >>> token = client.login(
            ...     "user@example.com", "password123", namespace="public"
            ... )
            >>> client.set_token(token.access_token)
        """
        credentials = LoginCredentials(
            identity=username, password=password, namespace=namespace
        )
        response = self._make_request(
            "POST",
            "/api/login",
            data=credentials.model_dump(),
            use_auth=False,
        )

        token = self._parse_token_response(response)
        self._token = token.access_token
        try:
            self._token_data = jwt.decode(
                token.access_token, options={"verify_signature": False}
            )
        except Exception:
            self._token_data = None
        return token

    @staticmethod
    def _registration_payload(response: Any) -> Dict[str, Any]:
        """Pull the user object out of a registration response.

        ``POST /api/register`` answers with the bare user object. Some
        deployments wrap it as ``{"user": {...}}``, so both are accepted.
        """
        if not isinstance(response, dict):
            raise NetworkError(
                "Unexpected response format for user registration."
            )

        wrapped = response.get("user")
        if isinstance(wrapped, dict) and wrapped:
            return wrapped

        # A bare user object is identified by carrying an identifier; anything
        # else is a response shape this SDK does not understand.
        if response.get("id") or response.get("user_id"):
            return response

        raise NetworkError("Unexpected response format for user registration.")

    def register_user(
        self,
        username: str,
        email: str,
        password: str,
        namespace: str = "public",
        group: Optional[str] = None,
        **attributes: Any,
    ) -> User:
        """
        Register a new user.

        Args:
            username: Username (3-50 characters)
            email: User email address
            password: Password (minimum 8 characters)
            namespace: User namespace (default: "public")
            group: Group to place the new user in. Sent as a top-level field,
                which is where the server reads it from.
            **attributes: Additional user attributes

        Returns:
            Created User object

        Raises:
            AuthenticationError: If registration fails

        Example:
            >>> client = KeyrunesClient("https://keyrunes.example.com")
            >>> user = client.register_user(
            ...     username="newuser",
            ...     email="newuser@example.com",
            ...     password="securepass123",
            ...     namespace="my-app",
            ...     department="Engineering"
            ... )
        """
        registration = UserRegistration(
            username=username,
            email=email,
            password=password,
            namespace=namespace,
            attributes=attributes,
        )
        data = registration.model_dump()
        if group is not None:
            data["group"] = group

        response = self._make_request(
            "POST",
            ENDPOINT_REGISTER,
            data=data,
            use_auth=False,
        )

        return self._normalize_user(self._registration_payload(response))

    def register_admin(
        self,
        username: str,
        email: str,
        password: str,
        admin_key: str,
        namespace: str = "public",
        **attributes: Any,
    ) -> User:
        """
        Register a new admin user.

        Args:
            username: Username (3-50 characters)
            email: Admin email address
            password: Password (minimum 8 characters)
            admin_key: Admin registration key
            namespace: User namespace (default: "public")
            **attributes: Additional user attributes

        Returns:
            Created User object with admin privileges

        Raises:
            AuthenticationError: If registration fails
            AuthorizationError: If admin key is invalid

        Example:
            >>> client = KeyrunesClient("https://keyrunes.example.com")
            >>> admin = client.register_admin(
            ...     username="adminuser",
            ...     email="admin@example.com",
            ...     password="securepass123",
            ...     admin_key="secret-admin-key"
            ... )
        """
        registration = AdminRegistration(
            username=username,
            email=email,
            password=password,
            admin_key=admin_key,
            namespace=namespace,
            attributes=attributes,
        )
        response = self._make_request(
            "POST",
            ENDPOINT_REGISTER,
            data=registration.model_dump(),
            use_auth=False,
        )

        return self._normalize_user(self._registration_payload(response))

    def has_group(self, user_id: str, group_id: str) -> bool:
        """
        Check if a user belongs to a specific group.

        Args:
            user_id: User ID to check
            group_id: Group ID to verify membership

        Returns:
            True if user belongs to the group, False otherwise

        Raises:
            AuthenticationError: If not authenticated
            GroupNotFoundError: If group doesn't exist

        Example:
            >>> client = KeyrunesClient("https://keyrunes.example.com")
            >>> client.login("user@example.com", "password")
            >>> has_access = client.has_group("user123", "admins")
            >>> if has_access:
            ...     print("User has admin access")
        """
        if not self._token:
            raise AuthenticationError("Not authenticated. Please login first.")

        token_user_id = (
            str(self._token_data.get("sub", "")) if self._token_data else None
        )

        if token_user_id and str(user_id) == token_user_id:
            groups = (
                self._token_data.get("groups", []) if self._token_data else []
            )
            return group_id in groups

        try:
            response = self._make_request(
                "GET",
                f"/api/users/{user_id}/groups/{group_id}",
            )
            check = GroupCheck(**response)
            return check.has_access
        except UserNotFoundError:
            # The self-lookup above already returned for the authenticated
            # user, so reaching here always means a genuine miss.
            raise GroupNotFoundError(
                f"Group '{group_id}' not found or user not in group"
            )

    def get_user(self, user_id: str) -> User:
        """
        Get user information by ID.

        Args:
            user_id: User ID

        Returns:
            User object

        Raises:
            AuthenticationError: If not authenticated
            UserNotFoundError: If user doesn't exist

        Example:
            >>> client = KeyrunesClient("https://keyrunes.example.com")
            >>> client.login("user@example.com", "password")
            >>> user = client.get_user("user123")
            >>> print(user.username)
        """
        if not self._token:
            raise AuthenticationError("Not authenticated. Please login first.")

        token_user_id = (
            str(self._token_data.get("sub", "")) if self._token_data else None
        )

        if token_user_id and str(user_id) == token_user_id and self._token_data:
            return self._user_from_token_claims()

        # The claims shortcut above already handled the authenticated user, so
        # a 404 here is always a genuine miss and is propagated as such.
        response = self._make_request("GET", f"/api/users/{user_id}")
        return self._normalize_user(response)

    def get_current_user(self, force_refresh: bool = False) -> User:
        """
        Get currently authenticated user information.

        Args:
            force_refresh: Ask the server even when the token's own claims
                could answer. Required whenever the answer is used to decide
                whether the token is still good: the claims shortcut reads a
                token the SDK never verified, so it says nothing about whether
                the server still accepts it (revoked, expired, or signed with
                another key).

        Returns:
            User object for authenticated user

        Raises:
            AuthenticationError: If not authenticated

        Example:
            >>> client = KeyrunesClient("https://keyrunes.example.com")
            >>> client.login("user@example.com", "password")
            >>> me = client.get_current_user()
            >>> print(f"Logged in as: {me.username}")
        """
        if not self._token:
            raise AuthenticationError("Not authenticated. Please login first.")

        if self._token_data and not force_refresh:
            return self._user_from_token_claims()

        response = self._make_request("GET", ENDPOINT_ME)
        return self._normalize_user(response)

    def get_user_groups(self, user_id: Optional[str] = None) -> List[str]:
        """
        Get list of groups for a user.

        Args:
            user_id: User ID (if None, uses current user)

        Returns:
            List of group IDs

        Raises:
            AuthenticationError: If not authenticated

        Example:
            >>> client = KeyrunesClient("https://keyrunes.example.com")
            >>> client.login("user@example.com", "password")
            >>> groups = client.get_user_groups()
            >>> print(f"User belongs to: {groups}")
        """
        if user_id:
            user = self.get_user(user_id)
        else:
            user = self.get_current_user()

        return user.groups

    def set_token(self, token: str) -> None:
        """
        Set authentication token for subsequent requests.

        Args:
            token: JWT access token

        Example:
            >>> client = KeyrunesClient("https://keyrunes.example.com")
            >>> client.set_token("eyJhbGciOiJIUzI1NiIs...")
        """
        self._token = token
        try:
            self._token_data = jwt.decode(
                token, options={"verify_signature": False}
            )
        except Exception:
            self._token_data = None

    def refresh_token(self, token: Optional[str] = None) -> Token:
        """
        Exchange a still-valid token for a fresh one.

        Args:
            token: Token to exchange. Defaults to the client's current token.

        Returns:
            Token object carrying the new access token.

        Raises:
            InvalidTokenError: If no token is available to exchange
            AuthenticationError: If the server rejects the token
            NetworkError: If the request fails

        Example:
            >>> client = KeyrunesClient("https://keyrunes.example.com")
            >>> client.set_token("eyJhbGciOiJIUzI1NiIs...")
            >>> refreshed = client.refresh_token()
            >>> client.set_token(refreshed.access_token)
        """
        current = token or self._token
        if not current:
            raise InvalidTokenError("No token available to refresh.")

        response = self._make_request(
            "POST",
            ENDPOINT_REFRESH_TOKEN,
            data={"token": current},
            use_auth=False,
        )

        refreshed = self._parse_token_response(response)
        # Refreshing is only ever useful if the client keeps using the result,
        # so adopt it the way login() does.
        self.set_token(refreshed.access_token)
        return refreshed

    def change_password(self, current_password: str, new_password: str) -> None:
        """
        Change the password of whoever the current token identifies.

        The server also clears the account's ``first_login`` flag, which is
        what ``requires_password_change`` reports at login: changing the
        password here puts that warning away without a second call.

        Nothing in the body says whose password it is — the token does. A body
        that chose would make "change my password" mean "change anyone's".

        Args:
            current_password: The password being replaced. The server checks
                it before accepting the change.
            new_password: The new password. The server requires at least 8
                characters and answers 400 when it is shorter.

        Raises:
            InvalidTokenError: If the client has no token set
            NetworkError: If the server refuses — wrong current password, or a
                new password it will not accept. The server answers **400** for
                both, which this client maps to ``NetworkError`` like any
                other non-401/403/404 status. The server's wording survives,
                because "invalid current password" and "password too short" call
                for opposite fixes.

        Example:
            >>> client = KeyrunesClient("https://keyrunes.example.com")
            >>> client.set_token("eyJhbGciOiJIUzI1NiIs...")
            >>> client.change_password("old-secret", "a-longer-new-secret")
        """
        if not self._token:
            raise InvalidTokenError("No token available to change a password.")

        self._make_request(
            "POST",
            ENDPOINT_CHANGE_PASSWORD,
            data={
                "current_password": current_password,
                "new_password": new_password,
            },
        )

    def clear_token(self) -> None:
        """
        Clear authentication token.

        Example:
            >>> client = KeyrunesClient("https://keyrunes.example.com")
            >>> client.clear_token()
        """
        self._token = None
        self._token_data = None

    def close(self) -> None:
        """
        Close HTTP client.

        Example:
            >>> client = KeyrunesClient("https://keyrunes.example.com")
            >>> # ... use client ...
            >>> client.close()
        """
        self._client.close()

    def __enter__(self) -> "KeyrunesClient":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()
