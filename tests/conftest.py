"""Pytest configuration and fixtures."""

import os
from unittest.mock import MagicMock, Mock

import pytest
from faker import Faker
from hypothesis import settings as hypothesis_settings

from keyrunes_sdk.client import KeyrunesClient
from keyrunes_sdk.models import Token, User

fake = Faker()

# Hypothesis profiles.
#
# ``fast`` is what the mutation runs (``mutmut``) use: a mutant only has to be
# distinguished from the original, and the whole suite is re-run once per
# mutant, so breadth is traded for wall-clock time.
# ``derandomize`` + ``database=None`` keep every mutant judged against the
# exact same examples, so a mutant is reported as survived only when the suite
# genuinely cannot tell it apart from the original.
hypothesis_settings.register_profile(
    "fast",
    max_examples=15,
    deadline=None,
    derandomize=True,
    database=None,
)
hypothesis_settings.register_profile("dev", max_examples=50, deadline=None)
hypothesis_settings.register_profile("ci", max_examples=300, deadline=None)
hypothesis_settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "dev"))


@pytest.fixture
def base_url() -> str:
    """Return base URL for tests."""
    return "https://keyrunes.example.com"


@pytest.fixture
def api_key() -> str:
    """Return API key for tests."""
    return "test-api-key-12345"


@pytest.fixture
def mock_client(base_url: str, api_key: str) -> KeyrunesClient:
    """Return mocked Keyrunes client."""
    client = KeyrunesClient(base_url=base_url, api_key=api_key)
    client._make_request = MagicMock()  # setup
    return client


@pytest.fixture
def sample_user() -> User:
    """Return sample user for testing."""
    return User(
        id="user123",
        username="testuser",
        email="testuser@example.com",
        groups=["users", "developers"],
        is_active=True,
        is_admin=False,
    )


@pytest.fixture
def sample_admin() -> User:
    """Return sample admin user for testing."""
    return User(
        id="admin123",
        username="adminuser",
        email="admin@example.com",
        groups=["admins", "users"],
        is_active=True,
        is_admin=True,
    )


@pytest.fixture
def sample_token(sample_user: User) -> Token:
    """Return sample token for testing."""
    return Token(
        access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test",
        token_type="bearer",
        expires_in=3600,
        user=sample_user,
    )


@pytest.fixture
def mock_response() -> Mock:
    """Return mock response object."""
    response = Mock()
    response.status_code = 200
    response.json.return_value = {}
    return response
