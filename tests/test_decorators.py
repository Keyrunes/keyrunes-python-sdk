"""Tests for Keyrunes SDK decorators."""

import pytest
from unittest.mock import MagicMock

from keyrunes_sdk.decorators import require_group, require_admin
from keyrunes_sdk.exceptions import AuthorizationError
from keyrunes_sdk.models import User
from tests.factories import UserFactory, AdminUserFactory


class TestRequireGroupDecorator:
    """Tests for require_group decorator."""

    def test_require_group_user_has_access(self, mock_client) -> None:
        """Test decorator allows access when user has group."""
        mock_client.has_group = MagicMock(return_value=True)

        @require_group("admins", client=mock_client)
        def admin_function(user_id: str) -> str:
            return f"Admin action for {user_id}"

        result = admin_function(user_id="user123")

        assert result == "Admin action for user123"
        mock_client.has_group.assert_called_once_with("user123", "admins")

    def test_require_group_user_no_access(self, mock_client) -> None:
        """Test decorator denies access when user doesn't have group."""
        mock_client.has_group = MagicMock(return_value=False)

        @require_group("admins", client=mock_client)
        def admin_function(user_id: str) -> str:
            return f"Admin action for {user_id}"

        with pytest.raises(AuthorizationError) as exc_info:
            admin_function(user_id="user123")

        assert "does not belong to any of the required groups" in str(exc_info.value)

    def test_require_group_multiple_groups_any(self, mock_client) -> None:
        """Test decorator with multiple groups (ANY match)."""
        mock_client.has_group = MagicMock(side_effect=lambda uid, gid: gid == "moderators")

        @require_group("admins", "moderators", client=mock_client, all_groups=False)
        def moderate_function(user_id: str) -> str:
            return f"Moderate action for {user_id}"

        result = moderate_function(user_id="user123")

        assert result == "Moderate action for user123"

    def test_require_group_multiple_groups_all(self, mock_client) -> None:
        """Test decorator with multiple groups (ALL required)."""
        mock_client.has_group = MagicMock(return_value=True)

        @require_group("admins", "verified", client=mock_client, all_groups=True)
        def sensitive_function(user_id: str) -> str:
            return f"Sensitive action for {user_id}"

        result = sensitive_function(user_id="user123")

        assert result == "Sensitive action for user123"
        assert mock_client.has_group.call_count == 2

    def test_require_group_multiple_groups_all_missing_one(self, mock_client) -> None:
        """Test decorator with ALL groups required but user missing one."""
        mock_client.has_group = MagicMock(side_effect=lambda uid, gid: gid == "admins")

        @require_group("admins", "verified", client=mock_client, all_groups=True)
        def sensitive_function(user_id: str) -> str:
            return f"Sensitive action for {user_id}"

        with pytest.raises(AuthorizationError) as exc_info:
            sensitive_function(user_id="user123")

        assert "does not have required group 'verified'" in str(exc_info.value)

    def test_require_group_from_kwargs(self, mock_client) -> None:
        """Test decorator gets client from kwargs."""
        mock_client.has_group = MagicMock(return_value=True)

        @require_group("admins")
        def admin_function(user_id: str, client) -> str:
            return f"Admin action for {user_id}"

        result = admin_function(user_id="user123", client=mock_client)

        assert result == "Admin action for user123"

    def test_require_group_no_client_provided(self) -> None:
        """Test decorator raises error when no client provided."""

        @require_group("admins")
        def admin_function(user_id: str) -> str:
            return f"Admin action for {user_id}"

        with pytest.raises(ValueError) as exc_info:
            admin_function(user_id="user123")

        assert "KeyrunesClient not provided" in str(exc_info.value)

    def test_require_group_no_user_id(self, mock_client) -> None:
        """Test decorator raises error when user_id not provided."""

        @require_group("admins", client=mock_client)
        def admin_function() -> str:
            return "Admin action"

        with pytest.raises(ValueError) as exc_info:
            admin_function()

        assert "User ID not found" in str(exc_info.value)

    def test_require_group_custom_user_id_param(self, mock_client) -> None:
        """Test decorator with custom user_id parameter name."""
        mock_client.has_group = MagicMock(return_value=True)

        @require_group("admins", client=mock_client, user_id_param="target_user")
        def admin_function(target_user: str) -> str:
            return f"Admin action for {target_user}"

        result = admin_function(target_user="user123")

        assert result == "Admin action for user123"
        mock_client.has_group.assert_called_once_with("user123", "admins")

    def test_require_group_user_id_from_args(self, mock_client) -> None:
        """Test decorator gets user_id from positional args."""
        mock_client.has_group = MagicMock(return_value=True)

        @require_group("admins", client=mock_client)
        def admin_function(user_id: str, action: str) -> str:
            return f"{action} for {user_id}"

        result = admin_function("user123", "Delete")

        assert result == "Delete for user123"
        mock_client.has_group.assert_called_once_with("user123", "admins")


class TestRequireAdminDecorator:
    """Tests for require_admin decorator."""

    def test_require_admin_user_is_admin(self, mock_client) -> None:
        """Test decorator allows access for admin user."""
        admin_user = AdminUserFactory()
        mock_client.get_user = MagicMock(return_value=admin_user)

        @require_admin(client=mock_client)
        def admin_function(user_id: str) -> str:
            return f"Admin action for {user_id}"

        result = admin_function(user_id="admin123")

        assert result == "Admin action for admin123"
        mock_client.get_user.assert_called_once_with("admin123")

    def test_require_admin_user_not_admin(self, mock_client) -> None:
        """Test decorator denies access for non-admin user."""
        regular_user = UserFactory(is_admin=False)
        mock_client.get_user = MagicMock(return_value=regular_user)

        @require_admin(client=mock_client)
        def admin_function(user_id: str) -> str:
            return f"Admin action for {user_id}"

        with pytest.raises(AuthorizationError) as exc_info:
            admin_function(user_id="user123")

        assert "does not have admin privileges" in str(exc_info.value)

    def test_require_admin_from_kwargs(self, mock_client) -> None:
        """Test decorator gets client from kwargs."""
        admin_user = AdminUserFactory()
        mock_client.get_user = MagicMock(return_value=admin_user)

        @require_admin()
        def admin_function(user_id: str, client) -> str:
            return f"Admin action for {user_id}"

        result = admin_function(user_id="admin123", client=mock_client)

        assert result == "Admin action for admin123"

    def test_require_admin_no_client(self) -> None:
        """Test decorator raises error when no client provided."""

        @require_admin()
        def admin_function(user_id: str) -> str:
            return f"Admin action for {user_id}"

        with pytest.raises(ValueError) as exc_info:
            admin_function(user_id="admin123")

        assert "KeyrunesClient not provided" in str(exc_info.value)

    def test_require_admin_no_user_id(self, mock_client) -> None:
        """Test decorator raises error when user_id not provided."""

        @require_admin(client=mock_client)
        def admin_function() -> str:
            return "Admin action"

        with pytest.raises(ValueError) as exc_info:
            admin_function()

        assert "User ID not found" in str(exc_info.value)

    def test_require_admin_custom_user_id_param(self, mock_client) -> None:
        """Test decorator with custom user_id parameter name."""
        admin_user = AdminUserFactory()
        mock_client.get_user = MagicMock(return_value=admin_user)

        @require_admin(client=mock_client, user_id_param="admin_id")
        def admin_function(admin_id: str) -> str:
            return f"Admin action for {admin_id}"

        result = admin_function(admin_id="admin123")

        assert result == "Admin action for admin123"

    def test_require_admin_user_id_from_args(self, mock_client) -> None:
        """Test decorator gets user_id from positional args."""
        admin_user = AdminUserFactory()
        mock_client.get_user = MagicMock(return_value=admin_user)

        @require_admin(client=mock_client)
        def admin_function(user_id: str, action: str) -> str:
            return f"{action} by {user_id}"

        result = admin_function("admin123", "System config")

        assert result == "System config by admin123"


class TestDecoratorIntegration:
    """Integration tests for decorators."""

    def test_multiple_decorators_combined(self, mock_client) -> None:
        """Test combining multiple decorators."""
        admin_user = AdminUserFactory(groups=["admins", "superusers"])
        mock_client.get_user = MagicMock(return_value=admin_user)
        mock_client.has_group = MagicMock(return_value=True)

        @require_admin(client=mock_client)
        @require_group("superusers", client=mock_client)
        def super_admin_function(user_id: str) -> str:
            return f"Super admin action for {user_id}"

        result = super_admin_function(user_id="admin123")

        assert result == "Super admin action for admin123"

    def test_decorator_preserves_function_metadata(self, mock_client) -> None:
        """Test that decorator preserves function name and docstring."""
        mock_client.has_group = MagicMock(return_value=True)

        @require_group("admins", client=mock_client)
        def my_function(user_id: str) -> str:
            """This is my function docstring."""
            return "result"

        assert my_function.__name__ == "my_function"
        assert my_function.__doc__ == "This is my function docstring."
