"""Factory Boy factories for testing."""

from datetime import datetime
from typing import Any

import factory
from factory import Faker, LazyAttribute
from faker import Faker as FakerInstance

from keyrunes_sdk.models import (
    User,
    Group,
    Token,
    UserRegistration,
    AdminRegistration,
    GroupCheck,
)


fake_instance = FakerInstance()


class UserFactory(factory.Factory):
    """Factory for User model."""

    class Meta:
        model = User

    id = Faker("uuid4")
    username = Faker("user_name")
    email = Faker("email")
    groups = LazyAttribute(lambda _: [fake_instance.word() for _ in range(2)])
    attributes = factory.Dict({})
    created_at = Faker("date_time_this_year")
    updated_at = Faker("date_time_this_month")
    is_active = True
    is_admin = False


class AdminUserFactory(UserFactory):
    """Factory for Admin User."""

    is_admin = True
    groups = LazyAttribute(lambda _: ["admins", fake_instance.word()])


class GroupFactory(factory.Factory):
    """Factory for Group model."""

    class Meta:
        model = Group

    id = Faker("uuid4")
    name = Faker("word")
    description = Faker("sentence")
    permissions = LazyAttribute(lambda _: [f"permission_{i}" for i in range(3)])
    created_at = Faker("date_time_this_year")


class TokenFactory(factory.Factory):
    """Factory for Token model."""

    class Meta:
        model = Token

    access_token = LazyAttribute(
        lambda _: f"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.{fake_instance.sha256()[:50]}"
    )
    token_type = "bearer"
    expires_in = 3600
    refresh_token = LazyAttribute(lambda _: fake_instance.sha256())
    user = factory.SubFactory(UserFactory)


class UserRegistrationFactory(factory.Factory):
    """Factory for UserRegistration model."""

    class Meta:
        model = UserRegistration

    username = Faker("user_name")
    email = Faker("email")
    password = LazyAttribute(lambda _: fake_instance.password(length=12))
    attributes = factory.Dict({})


class AdminRegistrationFactory(UserRegistrationFactory):
    """Factory for AdminRegistration model."""

    class Meta:
        model = AdminRegistration

    admin_key = LazyAttribute(lambda _: fake_instance.sha256()[:32])


class GroupCheckFactory(factory.Factory):
    """Factory for GroupCheck model."""

    class Meta:
        model = GroupCheck

    user_id = Faker("uuid4")
    group_id = Faker("word")
    has_access = True
    checked_at = factory.LazyFunction(datetime.utcnow)
