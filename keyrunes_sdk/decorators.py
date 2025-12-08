"""Decorators for Keyrunes authorization."""

from functools import wraps
from typing import Callable, Any, Optional

from keyrunes_sdk.client import KeyrunesClient
from keyrunes_sdk.exceptions import AuthorizationError, UserNotFoundError


def _get_client(
    client: Optional[KeyrunesClient], kwargs: dict
) -> KeyrunesClient:
    """
    Get client from decorator, kwargs, or global config.

    Args:
        client: Client passed to decorator
        kwargs: Function kwargs that might contain 'client'

    Returns:
        KeyrunesClient instance

    Raises:
        ValueError: If no client is available
    """
    if client:
        return client

    if "client" in kwargs:
        return kwargs["client"]

    from keyrunes_sdk.config import get_global_client

    global_client = get_global_client()
    if global_client:
        return global_client

    raise ValueError(
        "KeyrunesClient not provided. Either:\n"
        "1. Pass 'client' parameter to decorator: "
        "@require_group('admins', client=client)\n"
        "2. Pass 'client' in function kwargs: "
        "func(user_id='123', client=client)\n"
        "3. Configure global client: "
        "configure('https://keyrunes.example.com')"
    )


def require_group(
    *group_ids: str,
    client: Optional[KeyrunesClient] = None,
    user_id_param: str = "user_id",
    all_groups: bool = False,
) -> Callable:
    """
    Decorator to require user membership in one or more groups.

    This decorator checks if a user belongs to the specified group(s) before
    executing the decorated function. If the user doesn't have the required
    group membership, an AuthorizationError is raised.

    Args:
        *group_ids: One or more group IDs to check
        client: KeyrunesClient instance
            (if None, expects 'client' in kwargs)
        user_id_param: Name of the parameter containing user_id
            (default: 'user_id')
        all_groups: If True, user must belong to ALL groups;
            if False, ANY group (default: False)

    Returns:
        Decorated function

    Raises:
        AuthorizationError: If user doesn't have required group membership
        ValueError: If client is not provided

    Example:
        >>> @require_group("admins")
        ... def delete_user(user_id: str, client: KeyrunesClient):
        ...     # This function only executes if user is in 'admins' group
        ...     pass

        >>> @require_group("admins", "moderators", all_groups=False)
        ... def moderate_content(user_id: str, client: KeyrunesClient):
        ...     # User needs to be in 'admins' OR 'moderators'
        ...     pass

        >>> @require_group("admins", "verified", all_groups=True)
        ... def sensitive_operation(user_id: str, client: KeyrunesClient):
        ...     # User needs to be in BOTH 'admins' AND 'verified'
        ...     pass

        >>> # Using with a custom client
        >>> my_client = KeyrunesClient("https://keyrunes.example.com")
        >>> my_client.login("admin@example.com", "password")
        >>>
        >>> @require_group("admins", client=my_client)
        ... def admin_only_function(user_id: str):
        ...     print(f"Admin function for user {user_id}")
        >>>
        >>> admin_only_function(user_id="user123")
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            keyrunes_client = _get_client(client, kwargs)

            user_id = kwargs.get(user_id_param)

            if not user_id:
                import inspect

                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())

                if user_id_param in param_names:
                    param_index = param_names.index(user_id_param)
                    if param_index < len(args):
                        user_id = args[param_index]

            if not user_id:
                raise ValueError(
                    f"User ID not found. Expected parameter "
                    f"'{user_id_param}' in function arguments."
                )

            if all_groups:
                for group_id in group_ids:
                    if not keyrunes_client.has_group(user_id, group_id):
                        raise AuthorizationError(
                            f"User '{user_id}' does not have required "
                            f"group '{group_id}'. All groups required: "
                            f"{group_ids}"
                        )
            else:
                has_any_group = False
                for group_id in group_ids:
                    if keyrunes_client.has_group(user_id, group_id):
                        has_any_group = True
                        break

                if not has_any_group:
                    raise AuthorizationError(
                        f"User '{user_id}' does not belong to any of "
                        f"the required groups: {group_ids}"
                    )

            return func(*args, **kwargs)

        return wrapper

    return decorator


def require_admin(
    client: Optional[KeyrunesClient] = None,
    user_id_param: str = "user_id",
) -> Callable:
    """
    Decorator to require admin privileges.

    Convenience decorator that checks if user has admin flag set.

    Args:
        client: KeyrunesClient instance
            (if None, expects 'client' in kwargs)
        user_id_param: Name of the parameter containing user_id
            (default: 'user_id')

    Returns:
        Decorated function

    Raises:
        AuthorizationError: If user doesn't have admin privileges

    Example:
        >>> @require_admin()
        ... def system_config(user_id: str, client: KeyrunesClient):
        ...     # Only admins can execute this
        ...     pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            keyrunes_client = _get_client(client, kwargs)

            user_id = kwargs.get(user_id_param)
            if not user_id:
                import inspect

                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())

                if user_id_param in param_names:
                    param_index = param_names.index(user_id_param)
                    if param_index < len(args):
                        user_id = args[param_index]

            if not user_id:
                raise ValueError(
                    f"User ID not found in parameter '{user_id_param}'"
                )

            token_user_id = (
                str(keyrunes_client._token_data.get("sub", ""))
                if keyrunes_client._token_data
                else None
            )

            if token_user_id and str(user_id) == token_user_id:
                groups = (
                    keyrunes_client._token_data.get("groups", [])
                    if keyrunes_client._token_data
                    else []
                )
                is_admin = (
                    "admins" in groups
                    or "superadmin" in groups
                    or any("admin" in str(g).lower() for g in groups)
                )
                if not is_admin:
                    raise AuthorizationError(
                        f"User '{user_id}' does not have admin privileges."
                    )
            else:
                try:
                    user = keyrunes_client.get_user(user_id)
                    if not user.is_admin:
                        raise AuthorizationError(
                            f"User '{user_id}' does not have admin "
                            f"privileges."
                        )
                except UserNotFoundError:
                    raise AuthorizationError(
                        f"User '{user_id}' not found or does not have "
                        f"admin privileges."
                    )

            return func(*args, **kwargs)

        return wrapper

    return decorator
