"""Tests for Keyrunes SDK global configuration."""

import pytest
from unittest.mock import MagicMock

from keyrunes_sdk.config import (
    configure,
    get_global_client,
    clear_global_client,
    get_config,
    _GlobalConfig,
)
from keyrunes_sdk.client import KeyrunesClient


class TestGlobalConfig:
    """Tests for _GlobalConfig class."""

    def setup_method(self) -> None:
        """Setup for each test - clear global client."""
        clear_global_client()

    def teardown_method(self) -> None:
        """Teardown after each test - clear global client."""
        clear_global_client()

    def test_initial_state(self) -> None:
        """Test that global client starts as None."""
        client = get_global_client()
        assert client is None

    def test_set_and_get_client(self, base_url: str) -> None:
        """Test setting and getting global client."""
        test_client = KeyrunesClient(base_url=base_url)
        config = get_config()
        config.set_client(test_client)

        retrieved_client = config.get_client()
        assert retrieved_client is test_client

    def test_configure(self, base_url: str) -> None:
        """Test configure function."""
        client = configure(base_url=base_url)

        assert isinstance(client, KeyrunesClient)
        assert client.base_url == base_url

        global_client = get_global_client()
        assert global_client is client

    def test_configure_with_api_key(self, base_url: str, api_key: str) -> None:
        """Test configure with API key."""
        client = configure(base_url=base_url, api_key=api_key)

        assert client.api_key == api_key

    def test_configure_with_timeout(self, base_url: str) -> None:
        """Test configure with custom timeout."""
        client = configure(base_url=base_url, timeout=60)

        assert client.timeout == 60

    def test_clear_global_client(self, base_url: str) -> None:
        """Test clearing global client."""
        configure(base_url=base_url)

        assert get_global_client() is not None

        clear_global_client()

        assert get_global_client() is None

    def test_multiple_configure_calls(self, base_url: str) -> None:
        """Test that multiple configure calls replace the client."""
        client1 = configure(base_url=base_url)
        client2 = configure(base_url="https://different.example.com")

        global_client = get_global_client()
        assert global_client is client2
        assert global_client is not client1

    def test_thread_safety(self, base_url: str) -> None:
        """Test thread-safe access to global client."""
        import threading

        results = []

        def set_client():
            client = KeyrunesClient(base_url=base_url)
            get_config().set_client(client)
            results.append(client)

        threads = [threading.Thread(target=set_client) for _ in range(10)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        assert len(results) == 10

        assert get_global_client() is not None


class TestGlobalConfigIntegrationWithDecorators:
    """Test integration of global config with decorators."""

    def setup_method(self) -> None:
        """Setup for each test."""
        clear_global_client()

    def teardown_method(self) -> None:
        """Teardown after each test."""
        clear_global_client()

    def test_decorator_uses_global_client(self, base_url: str, sample_user) -> None:
        """Test that decorators can use global client."""
        from keyrunes_sdk.decorators import require_group

        client = configure(base_url=base_url)
        client._make_request = MagicMock()
        client.has_group = MagicMock(return_value=True)

        @require_group("admins")
        def admin_function(user_id: str) -> str:
            return f"Admin action for {user_id}"

        result = admin_function(user_id="user123")
        assert result == "Admin action for user123"
        client.has_group.assert_called_once_with("user123", "admins")

    def test_decorator_prefers_explicit_client(self, base_url: str) -> None:
        """Test that explicit client takes precedence over global."""
        from keyrunes_sdk.decorators import require_group

        global_client = configure(base_url=base_url)
        global_client.has_group = MagicMock(return_value=True)

        explicit_client = KeyrunesClient(base_url=base_url)
        explicit_client.has_group = MagicMock(return_value=True)

        @require_group("admins", client=explicit_client)
        def admin_function(user_id: str) -> str:
            return f"Admin action for {user_id}"

        result = admin_function(user_id="user123")

        explicit_client.has_group.assert_called_once()
        global_client.has_group.assert_not_called()

    def test_decorator_with_no_client_fails(self) -> None:
        """Test that decorator fails when no client is available."""
        from keyrunes_sdk.decorators import require_group
        from keyrunes_sdk.exceptions import AuthorizationError

        @require_group("admins")
        def admin_function(user_id: str) -> str:
            return f"Admin action for {user_id}"

        with pytest.raises(ValueError) as exc_info:
            admin_function(user_id="user123")

        assert "KeyrunesClient not provided" in str(exc_info.value)


class TestGlobalConfigWithRequireAdmin:
    """Test global config with require_admin decorator."""

    def setup_method(self) -> None:
        """Setup for each test."""
        clear_global_client()

    def teardown_method(self) -> None:
        """Teardown after each test."""
        clear_global_client()

    def test_require_admin_uses_global_client(
        self, base_url: str, sample_admin
    ) -> None:
        """Test that require_admin can use global client."""
        from keyrunes_sdk.decorators import require_admin

        client = configure(base_url=base_url)
        client.get_user = MagicMock(return_value=sample_admin)

        @require_admin()
        def admin_only(user_id: str) -> str:
            return f"Admin only for {user_id}"

        result = admin_only(user_id="admin123")
        assert result == "Admin only for admin123"
        client.get_user.assert_called_once_with("admin123")


class TestConfigEdgeCases:
    """Test edge cases for configuration."""

    def setup_method(self) -> None:
        """Setup for each test."""
        clear_global_client()

    def teardown_method(self) -> None:
        """Teardown after each test."""
        clear_global_client()

    def test_clear_when_no_client(self) -> None:
        """Test clearing when no client is set."""
        clear_global_client()
        assert get_global_client() is None

    def test_multiple_clears(self, base_url: str) -> None:
        """Test multiple clear calls."""
        configure(base_url=base_url)
        clear_global_client()
        clear_global_client()

        assert get_global_client() is None

    def test_get_config_returns_same_instance(self) -> None:
        """Test that get_config always returns same instance."""
        config1 = get_config()
        config2 = get_config()

        assert config1 is config2
