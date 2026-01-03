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
                raise NetworkError(f"Request failed: {error_msg}")

            result: Dict[str, Any] = response.json()
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
        return User(**normalized)

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

    def register_user(
        self,
        username: str,
        email: str,
        password: str,
        namespace: str = "public",
        **attributes: Any,
    ) -> User:
        """
        Register a new user.

        Args:
            username: Username (3-50 characters)
            email: User email address
            password: Password (minimum 8 characters)
            namespace: User namespace (default: "public")
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
        response = self._make_request(
            "POST",
            "/api/register",
            data=registration.model_dump(),
            use_auth=False,
        )

        user_payload = (
            response.get("user") if isinstance(response, dict) else None
        )
        if not user_payload:
            raise NetworkError(
                "Unexpected response format for user registration."
            )

        return self._normalize_user(user_payload)

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
            "/api/register",
            data=registration.model_dump(),
            use_auth=False,
        )

        user_payload = (
            response.get("user") if isinstance(response, dict) else None
        )
        if not user_payload:
            raise NetworkError(
                "Unexpected response format for admin registration."
            )

        return self._normalize_user(user_payload)

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
            if token_user_id and str(user_id) == token_user_id:
                groups = (
                    self._token_data.get("groups", [])
                    if self._token_data
                    else []
                )
                return group_id in groups
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
            token_data = self._token_data
            user_data = {
                "id": str(token_data.get("sub", "")),
                "username": token_data.get("username", ""),
                "email": token_data.get("email", ""),
                "groups": token_data.get("groups", []),
            }
            return self._normalize_user(user_data)

        try:
            response = self._make_request("GET", f"/api/users/{user_id}")
            return self._normalize_user(response)
        except UserNotFoundError:
            if (
                token_user_id
                and str(user_id) == token_user_id
                and self._token_data
            ):
                token_data = self._token_data
                user_data = {
                    "id": str(token_data.get("sub", "")),
                    "username": token_data.get("username", ""),
                    "email": token_data.get("email", ""),
                    "groups": token_data.get("groups", []),
                }
                return self._normalize_user(user_data)
            raise

    def get_current_user(self) -> User:
        """
        Get currently authenticated user information.

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

        if self._token_data:
            token_data = self._token_data
            user_data = {
                "id": str(token_data.get("sub", "")),
                "username": token_data.get("username", ""),
                "email": token_data.get("email", ""),
                "groups": token_data.get("groups", []),
            }
            return self._normalize_user(user_data)

        try:
            response = self._make_request("GET", "/api/users/me")
            return self._normalize_user(response)
        except UserNotFoundError:
            if self._token_data:
                token_data = self._token_data
                user_data = {
                    "id": str(token_data.get("sub", "")),
                    "username": token_data.get("username", ""),
                    "email": token_data.get("email", ""),
                    "groups": token_data.get("groups", []),
                }
                return self._normalize_user(user_data)
            raise

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
