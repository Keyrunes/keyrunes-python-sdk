#!/usr/bin/env python3
"""
Local test script for Keyrunes SDK.

This script tests all library functionality against
a local Keyrunes instance running via Docker Compose.

Usage:
    python examples/test_local.py
"""

import os
import sys
import time
from typing import Optional

from examples.test_objects import (
    admin_registration_payload,
    login_payload,
    user_registration_payload,
)
from keyrunes_sdk import (
    AuthenticationError,
    AuthorizationError,
    KeyrunesClient,
    require_admin,
    require_group,
)

KEYRUNES_URL = os.getenv("KEYRUNES_BASE_URL", "http://localhost:3000")
ADMIN_KEY = os.getenv("ADMIN_KEY", "dev_admin_key_change_in_production")


def print_section(title: str) -> None:
    """Print section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def print_success(message: str) -> None:
    """Print success message."""
    print(f"[OK] {message}")


def print_error(message: str) -> None:
    """Print error message."""
    print(f"[ERROR] {message}")


def print_info(message: str) -> None:
    """Print info message."""
    print(f"[INFO] {message}")


def wait_for_keyrunes(url: str, timeout: int = 30) -> bool:
    """Wait for Keyrunes to be available."""
    from urllib.parse import urljoin

    import httpx

    health_url = urljoin(url.rstrip("/") + "/", "api/health")
    print_info(f"Waiting for Keyrunes health at {health_url}...")

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with httpx.Client(timeout=2) as client:
                response = client.get(health_url)
            if response.status_code == 200:
                print_success("Keyrunes is available!")
                return True
        except httpx.RequestError:
            time.sleep(2)
            print(".", end="", flush=True)

    print_error(f"Timeout: Keyrunes did not respond after {timeout}s")
    return False


def test_user_registration(client: KeyrunesClient) -> Optional[tuple]:
    """Test user registration."""
    print_section("Test 1: User Registration")

    try:
        user_data = user_registration_payload()
        user = client.register_user(**user_data)

        print_success(f"User registered: {user.username} ({user.email})")
        print_info(f"User ID: {user.id}")
        print_info(f"Groups: {user.groups}")
        print_info(f"Attributes: {user.attributes}")

        return (user.id, user_data)

    except Exception as e:
        print_error(f"Failed to register user: {e}")
        return None


def test_user_login(client: KeyrunesClient, user_data: dict) -> bool:
    """Test user login."""
    print_section("Test 2: User Login")

    try:
        login_data = login_payload(
            email=user_data["email"], password=user_data["password"]
        )
        token = client.login(login_data["identity"], login_data["password"])

        print_success("Login successful!")
        print_info(f"Token Type: {token.token_type}")
        print_info(f"Expires In: {token.expires_in}s")
        print_info(f"Access Token: {token.access_token[:50]}...")

        if token.user:
            print_info(f"User: {token.user.username} ({token.user.email})")

        return True

    except AuthenticationError as e:
        print_error(f"Authentication failed: {e}")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False


def test_admin_registration(client: KeyrunesClient) -> Optional[tuple]:
    """Test admin registration."""
    print_section("Test 3: Admin Registration")

    try:
        admin_data = admin_registration_payload(admin_key=ADMIN_KEY)
        admin = client.register_admin(**admin_data)

        print_success(f"Admin registered: {admin.username} ({admin.email})")
        print_info(f"Admin ID: {admin.id}")
        print_info(f"Is Admin: {admin.is_admin}")
        print_info(f"Groups: {admin.groups}")

        return (admin.id, admin_data)

    except Exception as e:
        print_error(f"Failed to register admin: {e}")
        return None


def test_get_current_user(client: KeyrunesClient) -> None:
    """Test getting current user."""
    print_section("Test 4: Get Current User")

    try:
        user = client.get_current_user()

        print_success(f"Current user retrieved: {user.username}")
        print_info(f"Email: {user.email}")
        print_info(f"Groups: {user.groups}")
        print_info(f"Is Active: {user.is_active}")
        print_info(f"Is Admin: {user.is_admin}")

    except Exception as e:
        print_error(f"Failed to get current user: {e}")


def test_group_check(client: KeyrunesClient, user_id: str) -> None:
    """Test group membership check."""
    print_section("Test 5: Group Verification")

    try:
        has_users_group = client.has_group(user_id, "users")
        print_success(f"User has 'users' group: {has_users_group}")

        has_admin_group = client.has_group(user_id, "admins")
        print_success(f"User has 'admins' group: {has_admin_group}")

    except Exception as e:
        print_error(f"Failed to verify groups: {e}")


def test_decorator_require_group(client: KeyrunesClient, user_id: str) -> None:
    """Test @require_group decorator."""
    print_section("Test 6: Decorator @require_group")

    @require_group("users", client=client)
    def user_function(user_id: str) -> str:
        return f"Function executed for user {user_id}"

    @require_group("admins", client=client)
    def admin_function(user_id: str) -> str:
        return f"Admin function executed for {user_id}"

    try:
        result = user_function(user_id=user_id)
        print_success(f"Decorator allowed execution: {result}")
    except AuthorizationError as e:
        print_error(f"Decorator blocked execution: {e}")

    try:
        result = admin_function(user_id=user_id)
        print_error(f"Decorator should NOT have allowed: {result}")
    except AuthorizationError:
        print_success("Decorator correctly blocked access (user is not admin)")


def test_decorator_require_admin(
    client: KeyrunesClient, admin_id: str, user_id: str
) -> None:
    """Test @require_admin decorator."""
    print_section("Test 7: Decorator @require_admin")

    @require_admin(client=client)
    def admin_only_function(user_id: str) -> str:
        return f"Admin-only function executed for {user_id}"

    try:
        result = admin_only_function(user_id=admin_id)
        print_success(f"Admin passed: {result}")
    except AuthorizationError as e:
        print_error(f"Admin was blocked (should not): {e}")
    except UserNotFoundError as e:
        print_error(f"Admin user not found: {e}")

    try:
        result = admin_only_function(user_id=user_id)
        print_error(f"Normal user should NOT have passed: {result}")
    except AuthorizationError:
        print_success("Normal user was correctly blocked")


def test_get_user_groups(client: KeyrunesClient) -> None:
    """Test getting user groups."""
    print_section("Test 8: Get User Groups")

    try:
        groups = client.get_user_groups()
        print_success(f"Current user groups: {groups}")

    except Exception as e:
        print_error(f"Failed to get groups: {e}")


def test_context_manager(user_data: dict) -> None:
    """Test using client as context manager."""
    print_section("Test 9: Context Manager")

    try:
        login_data = login_payload(
            email=user_data["email"], password=user_data["password"]
        )
        with KeyrunesClient(base_url=KEYRUNES_URL) as client:
            token = client.login(login_data["identity"], login_data["password"])
            print_success("Context manager working correctly")
            print_info(f"Token obtained: {token.access_token[:30]}...")

    except Exception as e:
        print_error(f"Context manager failed: {e}")


def main() -> int:
    """Main test function."""
    print_section("Keyrunes SDK - Local Tests")
    print_info(f"Keyrunes URL: {KEYRUNES_URL}")
    print_info(f"Admin Key: {ADMIN_KEY[:10]}...")

    if not wait_for_keyrunes(KEYRUNES_URL):
        print_error("\nKeyrunes is not available.")
        print_info("Make sure Docker Compose is running:")
        print_info("  docker-compose up -d")
        return 1

    client = KeyrunesClient(base_url=KEYRUNES_URL)

    user_result = test_user_registration(client)
    if not user_result:
        print_error("\nCannot continue without user_id")
        return 1
    user_id, user_data = user_result

    if not test_user_login(client, user_data):
        print_error("\nCannot continue without login")
        return 1

    admin_result = test_admin_registration(client)
    if not admin_result:
        print_error("\nCannot continue without admin_id")
        return 1
    admin_id, admin_data = admin_result

    admin_client = KeyrunesClient(base_url=KEYRUNES_URL)
    admin_login_data = login_payload(
        email=admin_data["email"], password=admin_data["password"]
    )
    admin_client.login(
        admin_login_data["identity"], admin_login_data["password"]
    )

    if admin_client._token_data:
        admin_groups = admin_client._token_data.get("groups", [])
        if "superadmin" not in admin_groups:
            print_info(
                "Note: Admin may need to be manually added to superadmin group in database."
            )
            print_info("For testing, you can run:")
            print_info(
                f"  docker-compose exec -T postgres psql -U keyrunes -d keyrunes -c \"INSERT INTO user_groups (user_id, group_id) SELECT {admin_id}, group_id FROM groups WHERE name = 'superadmin' ON CONFLICT DO NOTHING;\""
            )
            print_info("Then login again to refresh the token.")

    test_get_current_user(client)
    test_group_check(client, user_id)
    test_decorator_require_group(client, user_id)
    test_decorator_require_admin(admin_client, admin_id, user_id)
    test_get_user_groups(client)
    test_context_manager(user_data)

    print_section("Tests Completed!")
    print_success("All tests were executed")
    print_info("\nTo stop Keyrunes:")
    print_info("  docker-compose down")

    return 0


if __name__ == "__main__":
    sys.exit(main())
