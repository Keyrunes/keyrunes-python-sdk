"""Global configuration and client management for Keyrunes SDK."""

from threading import Lock
from typing import Optional

from keyrunes_sdk.client import KeyrunesClient


class _GlobalConfig:
    """
    Thread-safe global configuration for Keyrunes SDK.

    This class manages a global KeyrunesClient instance that can be configured
    once and used throughout the application without passing it explicitly
    to decorators and functions.

    Example:
        >>> from keyrunes_sdk import configure, require_group
        >>>
        >>> # Configure once at application startup
        >>> configure(base_url="https://keyrunes.example.com")
        >>>
        >>> # Use decorators without passing client
        >>> @require_group("admins")
        ... def delete_user(user_id: str):
        ...     pass
    """

    def __init__(self) -> None:
        """Initialize global configuration."""
        self._client: Optional[KeyrunesClient] = None
        self._lock = Lock()

    def set_client(self, client: KeyrunesClient) -> None:
        """
        Set the global client instance.

        Args:
            client: KeyrunesClient instance to use globally

        Example:
            >>> from keyrunes_sdk import get_config
            >>> from keyrunes_sdk.client import KeyrunesClient
            >>>
            >>> client = KeyrunesClient("https://keyrunes.example.com")
            >>> get_config().set_client(client)
        """
        with self._lock:
            self._client = client

    def get_client(self) -> Optional[KeyrunesClient]:
        """
        Get the global client instance.

        Returns:
            Global KeyrunesClient instance or None if not configured

        Example:
            >>> from keyrunes_sdk import get_config
            >>>
            >>> client = get_config().get_client()
            >>> if client:
            ...     user = client.get_current_user()
        """
        with self._lock:
            return self._client

    def configure(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        organization_key: Optional[str] = None,
        timeout: int = 30,
    ) -> KeyrunesClient:
        """
        Configure and create global client instance.

        Args:
            base_url: Base URL of the Keyrunes API
            api_key: Optional API key for authentication
            organization_key: Optional Organization Key (required for v0.2.0+)
            timeout: Request timeout in seconds (default: 30)

        Returns:
            Configured KeyrunesClient instance

        Example:
            >>> from keyrunes_sdk import get_config
            >>>
            >>> client = get_config().configure(
            ...     base_url="https://keyrunes.example.com",
            ...     api_key="my-api-key"
            ... )
        """
        client = KeyrunesClient(
            base_url=base_url,
            api_key=api_key,
            organization_key=organization_key,
            timeout=timeout,
        )
        self.set_client(client)
        return client

    def clear(self) -> None:
        """
        Clear the global client instance.

        Example:
            >>> from keyrunes_sdk import get_config
            >>>
            >>> get_config().clear()
        """
        with self._lock:
            if self._client:
                self._client.close()
            self._client = None


_config = _GlobalConfig()


def get_config() -> _GlobalConfig:
    """
    Get the global configuration instance.

    Returns:
        Global configuration instance

    Example:
        >>> from keyrunes_sdk import get_config
        >>>
        >>> config = get_config()
        >>> config.configure(base_url="https://keyrunes.example.com")
    """
    return _config


def configure(
    base_url: str,
    api_key: Optional[str] = None,
    organization_key: Optional[str] = None,
    timeout: int = 30,
) -> KeyrunesClient:
    """
    Configure the global Keyrunes client.

    This is a convenience function that configures the global client instance.
    After calling this function, decorators will automatically use this client
    without needing to pass it explicitly.

    Args:
        base_url: Base URL of the Keyrunes API
        api_key: Optional API key for authentication
        organization_key: Optional Organization Key (required for v0.2.0+)
        timeout: Request timeout in seconds (default: 30)

    Returns:
        Configured KeyrunesClient instance

    Example:
        >>> from keyrunes_sdk import configure, require_group
        >>>
        >>> # Configure once at app startup
        >>> client = configure("https://keyrunes.example.com")
        >>> client.login("user@example.com", "password")
        >>>
        >>> # Now decorators work without passing client
        >>> @require_group("admins")
        ... def admin_only_function(user_id: str):
        ...     print(f"Admin function for {user_id}")
        >>>
        >>> admin_only_function(user_id="user123")
    """
    return _config.configure(
        base_url=base_url,
        api_key=api_key,
        organization_key=organization_key,
        timeout=timeout,
    )


def get_global_client() -> Optional[KeyrunesClient]:
    """
    Get the global client instance.

    Returns:
        Global KeyrunesClient instance or None if not configured

    Raises:
        RuntimeError: If client is not configured

    Example:
        >>> from keyrunes_sdk import configure, get_global_client
        >>>
        >>> configure("https://keyrunes.example.com")
        >>> client = get_global_client()
        >>> user = client.get_current_user()
    """
    return _config.get_client()


def clear_global_client() -> None:
    """
    Clear the global client instance.

    Example:
        >>> from keyrunes_sdk import clear_global_client
        >>>
        >>> clear_global_client()
    """
    _config.clear()
