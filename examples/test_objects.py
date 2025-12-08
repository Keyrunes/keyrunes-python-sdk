import os
import secrets
import string
from uuid import uuid4


def _suffix(value: str | None = None) -> str:
    return value or uuid4().hex[:6]


def _random_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def user_registration_payload(
    suffix: str | None = None, password: str | None = None
) -> dict:
    tag = _suffix(suffix)
    return {
        "username": f"user_{tag}",
        "email": f"user_{tag}@example.com",
        "password": password or _random_password(),
        "department": "Engineering",
        "role": "Developer",
    }


def admin_registration_payload(
    suffix: str | None = None,
    admin_key: str | None = None,
    password: str | None = None,
) -> dict:
    tag = _suffix(suffix)
    return {
        "username": f"admin_{tag}",
        "email": f"admin_{tag}@example.com",
        "password": password or _random_password(),
        "admin_key": admin_key
        or os.getenv("ADMIN_KEY", "dev_admin_key_change_in_production"),
    }


def login_payload(email: str, password: str) -> dict:
    return {"identity": email, "password": password}


__all__ = [
    "user_registration_payload",
    "admin_registration_payload",
    "login_payload",
]
