"""Tests for Keyrunes SDK client."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import httpx

from keyrunes_sdk.client import KeyrunesClient
from keyrunes_sdk.models import User, Token
from keyrunes_sdk.exceptions import (
    AuthenticationError,
    AuthorizationError,
    UserNotFoundError,
    GroupNotFoundError,
    NetworkError,
)
from tests.factories import UserFactory, TokenFactory


class TestKeyrunesClient:
    """Tests for KeyrunesClient."""

    def test_init(self, base_url: str, api_key: str) -> None:
        """Test client initialization."""
        client = KeyrunesClient(base_url=base_url, api_key=api_key)

        assert client.base_url == base_url
        assert client.api_key == api_key
        assert client.timeout == 30
        assert client._token is None

    def test_init_strips_trailing_slash(self, api_key: str) -> None:
        """Test that trailing slash is stripped from base URL."""
        client = KeyrunesClient(
            base_url="https://keyrunes.example.com/",
            api_key=api_key,
        )

        assert client.base_url == "https://keyrunes.example.com"

    def test_set_token(self, mock_client: KeyrunesClient) -> None:
        """Test setting authentication token."""
        token = "test-token-123"
        mock_client.set_token(token)

        assert mock_client._token == token

    def test_clear_token(self, mock_client: KeyrunesClient) -> None:
        """Test clearing authentication token."""
        mock_client._token = "test-token"
        mock_client.clear_token()

        assert mock_client._token is None

    def test_context_manager(self, base_url: str) -> None:
        """Test using client as context manager."""
        with KeyrunesClient(base_url=base_url) as client:
            assert isinstance(client, KeyrunesClient)

    @patch("keyrunes_sdk.client.httpx.Client.request")
    def test_make_request_success(
        self,
        mock_request: Mock,
        base_url: str,
    ) -> None:
        """Test successful API request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_request.return_value = mock_response

        client = KeyrunesClient(base_url=base_url)
        result = client._make_request("GET", "/api/v1/test")

        assert result == {"data": "test"}
        mock_request.assert_called_once()

    @patch("keyrunes_sdk.client.httpx.Client.request")
    def test_make_request_authentication_error(
        self,
        mock_request: Mock,
        base_url: str,
    ) -> None:
        """Test request with authentication error."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_request.return_value = mock_response

        client = KeyrunesClient(base_url=base_url)

        with pytest.raises(AuthenticationError):
            client._make_request("GET", "/api/v1/test")

    @patch("keyrunes_sdk.client.httpx.Client.request")
    def test_make_request_authorization_error(
        self,
        mock_request: Mock,
        base_url: str,
    ) -> None:
        """Test request with authorization error."""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_request.return_value = mock_response

        client = KeyrunesClient(base_url=base_url)

        with pytest.raises(AuthorizationError):
            client._make_request("GET", "/api/v1/test")

    @patch("keyrunes_sdk.client.httpx.Client.request")
    def test_make_request_not_found_error(
        self,
        mock_request: Mock,
        base_url: str,
    ) -> None:
        """Test request with not found error."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_request.return_value = mock_response

        client = KeyrunesClient(base_url=base_url)

        with pytest.raises(UserNotFoundError):
            client._make_request("GET", "/api/v1/test")

    @patch("keyrunes_sdk.client.httpx.Client.request")
    def test_make_request_network_error(
        self,
        mock_request: Mock,
        base_url: str,
    ) -> None:
        """Test request with network error."""
        mock_request.side_effect = httpx.RequestError("Network error")

        client = KeyrunesClient(base_url=base_url)

        with pytest.raises(NetworkError):
            client._make_request("GET", "/api/v1/test")


class TestClientAuthentication:
    """Tests for authentication methods."""

    def test_login_success(
        self,
        mock_client: KeyrunesClient,
        sample_token: Token,
    ) -> None:
        """Test successful login."""
        mock_client._make_request.return_value = sample_token.model_dump()

        token = mock_client.login("testuser", "password123")

        assert isinstance(token, Token)
        assert token.access_token == sample_token.access_token
        assert mock_client._token == sample_token.access_token

    def test_login_sets_token(
        self,
        mock_client: KeyrunesClient,
        sample_token: Token,
    ) -> None:
        """Test that login sets token automatically."""
        mock_client._make_request.return_value = sample_token.model_dump()

        mock_client.login("testuser", "password123")

        assert mock_client._token == sample_token.access_token


class TestClientUserManagement:
    """Tests for user management methods."""

    def test_register_user_success(
        self,
        mock_client: KeyrunesClient,
        sample_user: User,
    ) -> None:
        """Test successful user registration."""
        mock_client._make_request.return_value = {"user": sample_user.model_dump()}

        user = mock_client.register_user(
            username="newuser",
            email="newuser@example.com",
            password="password123",
        )

        assert isinstance(user, User)
        assert user.username == sample_user.username
        assert user.email == sample_user.email

    def test_register_user_with_attributes(
        self,
        mock_client: KeyrunesClient,
        sample_user: User,
    ) -> None:
        """Test user registration with attributes."""
        mock_client._make_request.return_value = {"user": sample_user.model_dump()}

        user = mock_client.register_user(
            username="newuser",
            email="newuser@example.com",
            password="password123",
            department="Engineering",
            role="Developer",
        )

        assert isinstance(user, User)
        mock_client._make_request.assert_called_once()

    def test_register_admin_success(
        self,
        mock_client: KeyrunesClient,
        sample_admin: User,
    ) -> None:
        """Test successful admin registration."""
        mock_client._make_request.return_value = {"user": sample_admin.model_dump()}

        admin = mock_client.register_admin(
            username="adminuser",
            email="admin@example.com",
            password="password123",
            admin_key="secret-key",
        )

        assert isinstance(admin, User)
        assert admin.is_admin is True

    def test_register_user_normalizes_payload(self, base_url: str) -> None:
        client = KeyrunesClient(base_url=base_url)
        client._make_request = Mock(
            return_value={
                "user": {
                    "id": "1",
                    "username": "testuser",
                    "email": "testuser@example.com",
                    "groups": [],
                }
            }
        )

        user = client.register_user(username="testuser", email="testuser@example.com", password="pass12345")

        assert isinstance(user, User)
        assert user.id == "1"

    def test_register_admin_normalizes_payload(self, base_url: str) -> None:
        client = KeyrunesClient(base_url=base_url)
        client._make_request = Mock(
            return_value={
                "user": {
                    "external_id": "abc",
                    "username": "adminu",
                    "email": "admin@example.com",
                    "groups": ["admins"],
                }
            }
        )

        admin = client.register_admin(
            username="adminu",
            email="admin@example.com",
            password="pass12345",
            admin_key="key",
        )

        assert isinstance(admin, User)
        assert admin.id == "abc"
        assert admin.is_admin is True

    def test_get_user(
        self,
        mock_client: KeyrunesClient,
        sample_user: User,
    ) -> None:
        """Test getting user by ID."""
        mock_client._token = "test-token"
        mock_client._token_data = {"sub": "user123", "username": "testuser", "email": "testuser@example.com", "groups": []}
        mock_client._make_request.return_value = sample_user.model_dump()

        user = mock_client.get_user("user123")

        assert isinstance(user, User)
        assert user.id == sample_user.id

    def test_get_current_user(
        self,
        mock_client: KeyrunesClient,
        sample_user: User,
    ) -> None:
        """Test getting current authenticated user."""
        mock_client._token = "test-token"
        mock_client._token_data = {
            "sub": "user123",
            "username": sample_user.username,
            "email": sample_user.email,
            "groups": sample_user.groups,
        }

        user = mock_client.get_current_user()

        assert isinstance(user, User)
        assert user.id == "user123"
        assert user.username == sample_user.username

    def test_normalize_user_external_id(self, base_url: str) -> None:
        client = KeyrunesClient(base_url=base_url)
        data = {
            "external_id": "ext-1",
            "username": "user",
            "email": "user@example.com",
            "groups": ["admins"],
        }

        user = client._normalize_user(data)

        assert user.id == "ext-1"
        assert user.is_admin is True

    def test_parse_token_response_token_key(self, base_url: str, sample_user: User) -> None:
        client = KeyrunesClient(base_url=base_url)
        payload = {
            "token": "abc",
            "user": {
                "id": sample_user.id,
                "username": sample_user.username,
                "email": sample_user.email,
                "groups": sample_user.groups,
            },
        }

        token = client._parse_token_response(payload)

        assert token.access_token == "abc"
        assert token.user is not None
        assert token.user.id == sample_user.id

    def test_parse_token_response_access_token(self, base_url: str, sample_user: User) -> None:
        client = KeyrunesClient(base_url=base_url)
        payload = {
            "access_token": "xyz",
            "token_type": "bearer",
            "expires_in": 1000,
            "user": {
                "id": sample_user.id,
                "username": sample_user.username,
                "email": sample_user.email,
                "groups": sample_user.groups,
            },
        }

        token = client._parse_token_response(payload)

        assert token.access_token == "xyz"
        assert token.token_type == "bearer"


class TestClientGroupManagement:
    """Tests for group management methods."""

    def test_has_group_true(self, mock_client: KeyrunesClient) -> None:
        """Test checking group membership - user has group."""
        mock_client._token = "test-token"
        mock_client._token_data = {"sub": "user123", "username": "testuser", "email": "testuser@example.com", "groups": ["admins"]}
        mock_client._make_request.return_value = {
            "user_id": "user123",
            "group_id": "admins",
            "has_access": True,
        }

        result = mock_client.has_group("user123", "admins")

        assert result is True

    def test_has_group_false(self, mock_client: KeyrunesClient) -> None:
        """Test checking group membership - user doesn't have group."""
        mock_client._token = "test-token"
        mock_client._token_data = {"sub": "user123", "username": "testuser", "email": "testuser@example.com", "groups": []}
        mock_client._make_request.return_value = {
            "user_id": "user123",
            "group_id": "admins",
            "has_access": False,
        }

        result = mock_client.has_group("user123", "admins")

        assert result is False

    def test_has_group_not_found(self, mock_client: KeyrunesClient) -> None:
        """Test checking non-existent group."""
        mock_client._token = "test-token"
        mock_client._token_data = {"sub": "user123", "username": "testuser", "email": "testuser@example.com", "groups": []}
        mock_client._make_request.side_effect = UserNotFoundError("Not found")

        result = mock_client.has_group("user123", "nonexistent")
        assert result is False

    def test_get_user_groups(
        self,
        mock_client: KeyrunesClient,
        sample_user: User,
    ) -> None:
        """Test getting user groups."""
        mock_client._token = "test-token"
        mock_client._token_data = {"sub": "user123", "username": "testuser", "email": "testuser@example.com", "groups": sample_user.groups}
        mock_client._make_request.return_value = sample_user.model_dump()

        groups = mock_client.get_user_groups("user123")

        assert isinstance(groups, list)
        assert groups == sample_user.groups

    def test_get_user_groups_current_user(
        self,
        mock_client: KeyrunesClient,
        sample_user: User,
    ) -> None:
        """Test getting current user's groups."""
        mock_client._token = "test-token"
        mock_client._token_data = {"sub": "user123", "username": "testuser", "email": "testuser@example.com", "groups": sample_user.groups}

        groups = mock_client.get_user_groups()

        assert isinstance(groups, list)
        assert groups == sample_user.groups


class TestClientEdgeCases:
    """Tests for edge cases and error handling."""

    def test_login_with_empty_credentials(self, mock_client: KeyrunesClient) -> None:
        """Test login with empty credentials."""
        with pytest.raises(Exception):
            mock_client.login("", "")

    def test_client_close(self, base_url: str) -> None:
        """Test closing client."""
        client = KeyrunesClient(base_url=base_url)
        client.close()

        assert client._client is not None
