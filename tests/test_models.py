"""Tests for Keyrunes SDK models."""

import pytest
from pydantic import ValidationError

from keyrunes_sdk.models import (
    AdminRegistration,
    GroupCheck,
    LoginCredentials,
    Token,
    User,
    UserRegistration,
)
from tests.factories import (
    AdminRegistrationFactory,
    GroupFactory,
    TokenFactory,
    UserFactory,
    UserRegistrationFactory,
)


class TestUserModel:
    """Tests for User model."""

    def test_create_user(self) -> None:
        """Test creating a user."""
        user = UserFactory()

        assert user.id is not None
        assert user.username is not None
        assert user.email is not None
        assert isinstance(user.groups, list)
        assert isinstance(user.is_active, bool)
        assert isinstance(user.is_admin, bool)

    def test_user_with_groups(self) -> None:
        """Test user with multiple groups."""
        user = UserFactory(groups=["admins", "developers", "users"])

        assert len(user.groups) == 3
        assert "admins" in user.groups

    def test_user_default_values(self) -> None:
        """Test user default values."""
        user = User(
            id="test123",
            username="testuser",
            email="test@example.com",
        )

        assert user.groups == []
        assert user.attributes == {}
        assert user.is_active is True
        assert user.is_admin is False

    def test_user_email_validation(self) -> None:
        """Test email validation."""
        with pytest.raises(ValidationError):
            User(
                id="test123",
                username="testuser",
                email="invalid-email",
            )


class TestGroupModel:
    """Tests for Group model."""

    def test_create_group(self) -> None:
        """Test creating a group."""
        group = GroupFactory()

        assert group.id is not None
        assert group.name is not None
        assert isinstance(group.permissions, list)

    def test_group_with_permissions(self) -> None:
        """Test group with permissions."""
        group = GroupFactory(permissions=["read", "write", "delete"])

        assert len(group.permissions) == 3
        assert "read" in group.permissions


class TestTokenModel:
    """Tests for Token model."""

    def test_create_token(self) -> None:
        """Test creating a token."""
        token = TokenFactory()

        assert token.access_token is not None
        assert token.token_type == "bearer"
        assert token.expires_in == 3600

    def test_token_with_user(self) -> None:
        """Test token with user data."""
        user = UserFactory()
        token = TokenFactory(user=user)

        assert token.user is not None
        assert token.user.id == user.id
        assert token.user.username == user.username

    def test_token_default_type(self) -> None:
        """Test token default type."""
        token = Token(access_token="test-token")

        assert token.token_type == "bearer"


class TestUserRegistrationModel:
    """Tests for UserRegistration model."""

    def test_create_registration(self) -> None:
        """Test creating user registration."""
        registration = UserRegistrationFactory()

        assert registration.username is not None
        assert registration.email is not None
        assert registration.password is not None
        assert len(registration.password) >= 8

    def test_username_min_length(self) -> None:
        """Test username minimum length validation."""
        with pytest.raises(ValidationError):
            UserRegistration(
                username="ab",
                email="test@example.com",
                password="password123",
            )

    def test_username_max_length(self) -> None:
        """Test username maximum length validation."""
        with pytest.raises(ValidationError):
            UserRegistration(
                username="a" * 51,
                email="test@example.com",
                password="password123",
            )

    def test_password_min_length(self) -> None:
        """Test password minimum length validation."""
        with pytest.raises(ValidationError):
            UserRegistration(
                username="testuser",
                email="test@example.com",
                password="short",
            )

    def test_email_validation(self) -> None:
        """Test email validation in registration."""
        with pytest.raises(ValidationError):
            UserRegistration(
                username="testuser",
                email="invalid-email",
                password="password123",
            )

    def test_registration_with_attributes(self) -> None:
        """Test registration with additional attributes."""
        registration = UserRegistrationFactory(
            attributes={
                "department": "Engineering",
                "role": "Developer",
            }
        )

        assert registration.attributes["department"] == "Engineering"
        assert registration.attributes["role"] == "Developer"


class TestAdminRegistrationModel:
    """Tests for AdminRegistration model."""

    def test_create_admin_registration(self) -> None:
        """Test creating admin registration."""
        registration = AdminRegistrationFactory()

        assert registration.username is not None
        assert registration.email is not None
        assert registration.password is not None
        assert registration.admin_key is not None

    def test_admin_registration_requires_key(self) -> None:
        """Test admin registration requires admin key."""
        with pytest.raises(ValidationError):
            AdminRegistration(
                username="adminuser",
                email="admin@example.com",
                password="password123",
            )


class TestLoginCredentialsModel:
    """Tests for LoginCredentials model."""

    def test_create_credentials(self) -> None:
        """Test creating login credentials."""
        credentials = LoginCredentials(
            identity="testuser",
            password="password123",
        )

        assert credentials.identity == "testuser"
        assert credentials.password == "password123"


class TestGroupCheckModel:
    """Tests for GroupCheck model."""

    def test_create_group_check(self) -> None:
        """Test creating group check."""
        check = GroupCheck(
            user_id="user123",
            group_id="admins",
            has_access=True,
        )

        assert check.user_id == "user123"
        assert check.group_id == "admins"
        assert check.has_access is True
        assert check.checked_at is not None

    def test_group_check_default_timestamp(self) -> None:
        """Test group check has default timestamp."""
        check = GroupCheck(
            user_id="user123",
            group_id="admins",
            has_access=False,
        )

        assert check.checked_at is not None
