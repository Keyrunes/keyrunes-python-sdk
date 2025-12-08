#!/usr/bin/env python3
"""
Global Client usage example.

This example shows how to configure the client once and use decorators
without needing to pass the client in every function.
"""

from keyrunes_sdk import configure, require_group, require_admin, get_global_client


print("[INFO] Configuring Keyrunes SDK...")
client = configure(base_url="http://localhost:3000")

print("[INFO] Logging in...")
client.login("admin@example.com", "adminpass123")
print("[OK] Login successful!\n")


@require_group("admins")
def delete_user(user_id: str) -> str:
    """
    Function that requires 'admins' group.
    Note that we don't need to pass the client!
    """
    return f"User {user_id} deleted by admin"


@require_group("admins", "moderators", all_groups=False)
def moderate_content(user_id: str, content_id: str) -> str:
    """
    Function that requires 'admins' OR 'moderators' group.
    """
    return f"Content {content_id} moderated by {user_id}"


@require_admin()
def system_configuration(user_id: str) -> str:
    """
    Function that requires admin privileges.
    """
    return f"System configuration changed by {user_id}"


@require_group("admins", "verified", all_groups=True)
def sensitive_operation(user_id: str) -> str:
    """
    Function that requires BOTH 'admins' AND 'verified' groups.
    """
    return f"Sensitive operation executed by {user_id}"


def main():
    """Example usage of decorated functions."""

    print("=" * 60)
    print("  EXAMPLE: Elegant Usage with Global Client")
    print("=" * 60)
    print()

    print("[INFO] Current user:")
    current_user = get_global_client().get_current_user()
    print(f"   Username: {current_user.username}")
    print(f"   Email: {current_user.email}")
    print(f"   Groups: {current_user.groups}")
    print(f"   Is Admin: {current_user.is_admin}")
    print()

    print("[INFO] Executing decorated functions:")
    print()

    try:
        print("1. delete_user()")
        result = delete_user(user_id=current_user.id)
        print(f"   [OK] {result}")
        print()
    except Exception as e:
        print(f"   [ERROR] {e}")
        print()

    try:
        print("2. moderate_content()")
        result = moderate_content(user_id=current_user.id, content_id="post123")
        print(f"   [OK] {result}")
        print()
    except Exception as e:
        print(f"   [ERROR] {e}")
        print()

    try:
        print("3. system_configuration()")
        result = system_configuration(user_id=current_user.id)
        print(f"   [OK] {result}")
        print()
    except Exception as e:
        print(f"   [ERROR] {e}")
        print()

    try:
        print("4. sensitive_operation()")
        result = sensitive_operation(user_id=current_user.id)
        print(f"   [OK] {result}")
        print()
    except Exception as e:
        print(f"   [ERROR] {e}")
        print()

    print("=" * 60)
    print()
    print("[INFO] Global Client advantages:")
    print("   * Configure once at application startup")
    print("   * Use decorators without passing client")
    print("   * Cleaner and more elegant code")
    print("   * Fewer parameters in functions")
    print()


def example_multi_file_structure():
    """
    Example of how to organize in multiple files.

    config.py
    from keyrunes_sdk import configure

    def init_keyrunes():
        client = configure(base_url="https://keyrunes.example.com")
        client.login("user@example.com", "password")
        return client

    services/user_service.py
    from keyrunes_sdk import require_group, require_admin

    @require_group("admins")
    def delete_user(user_id: str):
        pass

    @require_admin()
    def system_config(user_id: str):
        pass

    main.py
    from config import init_keyrunes
    from services.user_service import delete_user, system_config

    Configure once
    init_keyrunes()

    Use anywhere!
    delete_user(user_id="123")
    system_config(user_id="admin123")
    """
    print("[INFO] Suggested project structure:")
    print()
    print("   my_project/")
    print("   ├── config.py              # Keyrunes configuration")
    print("   ├── main.py                # Entry point")
    print("   └── services/")
    print("       ├── __init__.py")
    print("       ├── user_service.py    # Functions with decorators")
    print("       └── admin_service.py   # More functions")
    print()
    print("   See this function's docstring for code example!")
    print()


if __name__ == "__main__":
    try:
        main()
        print()
        example_multi_file_structure()
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        print()
        print("Make sure that:")
        print("  1. Keyrunes is running: docker-compose up -d")
        print("  2. Admin was registered: poetry run python examples/test_local.py")
        sys.exit(1)
