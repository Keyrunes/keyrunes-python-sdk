#!/usr/bin/env python3
"""
Basic usage example for Keyrunes SDK.

This example shows how to use the main library features.
"""

import os
import sys

from keyrunes_sdk import KeyrunesClient, require_group


def main() -> None:
    """Basic usage example."""

    print("1. Creating client...")
    # NOTE: organization_key will be read from KEYRUNES_ORG_KEY env var
    client = KeyrunesClient(
        base_url="http://localhost:3000",
        organization_key=os.getenv("KEYRUNES_ORG_KEY"),
    )

    print("\n2. Registering new user...")
    user = client.register_user(
        username="johndoe",
        email="john@example.com",
        password="securepass123",
        namespace="public",
        department="Engineering",
        role="Developer",
    )
    print(f"   User created: {user.username} (ID: {user.id})")

    print("\n3. Logging in...")
    token = client.login(
        "john@example.com", "securepass123", namespace="public"
    )
    print(f"   Token obtained: {token.access_token[:30]}...")
    print(f"   Expires in: {token.expires_in}s")

    print("\n4. Getting user information...")
    current_user = client.get_current_user()
    print(f"   Username: {current_user.username}")
    print(f"   Email: {current_user.email}")
    print(f"   Groups: {current_user.groups}")

    print("\n5. Checking group...")
    has_access = client.has_group(user.id, "users")
    print(f"   User has 'users' group: {has_access}")

    print("\n6. Using decorators...")

    @require_group("users", client=client)
    def user_action(user_id: str) -> str:
        return f"Action executed for user {user_id}"

    try:
        result = user_action(user_id=user.id)
        print(f"   [OK] {result}")
    except Exception as e:
        print(f"   [ERROR] Error: {e}")

    print("\n7. Registering admin...")
    try:
        admin = client.register_admin(
            username="adminuser",
            email="admin@example.com",
            password="adminpass123",
            admin_key="dev_admin_key_change_in_production",
            namespace="public",
        )
        print(f"   Admin created: {admin.username} (ID: {admin.id})")
    except Exception as e:
        print(f"   [INFO] {e}")

    print("\n8. Using as context manager...")
    with KeyrunesClient(base_url="http://localhost:3000") as ctx_client:
        ctx_client.login(
            "john@example.com", "securepass123", namespace="public"
        )
        me = ctx_client.get_current_user()
        print(f"   Logged in user: {me.username}")

    print("\n[OK] Example completed successfully!")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        sys.exit(1)
