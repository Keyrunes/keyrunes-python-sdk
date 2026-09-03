"""Request-contract tests: what the SDK actually puts on the wire.

The existing suites mock ``_make_request`` wholesale, which means the HTTP
method, the URL, the JSON body and the auth header were never asserted — a
mutation run showed that replacing ``method=method`` with ``method=None`` in
``_make_request`` survived the whole suite. These tests pin the request shape
of every public operation by mocking only the httpx transport.
"""

from typing import Any, Dict, Optional
from unittest.mock import MagicMock

import pytest
from hypothesis import given
from hypothesis import strategies as st

from keyrunes_sdk.client import KeyrunesClient
from keyrunes_sdk.exceptions import (
    AuthenticationError,
    InvalidTokenError,
    NetworkError,
)
from tests.test_property_based import PROPERTY_SETTINGS

# A JWT-shaped token with no signature; the SDK decodes it without verifying.
# Payload: {"sub": "user123", "username": "john", "email": "john@example.com",
#           "groups": ["users"]}
JWT = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJzdWIiOiJ1c2VyMTIzIiwidXNlcm5hbWUiOiJqb2huIiwiZW1haWwiOiJqb2h"
    "uQGV4YW1wbGUuY29tIiwiZ3JvdXBzIjpbInVzZXJzIl19."
    "FbaCbE7yppVa5Xcx_m1wN1cpU0RjuFYt_yg-ZeYOZCo"
)

BASE_URL = "https://keyrunes.example.com"


def _client_with_transport(
    payload: Optional[Dict[str, Any]] = None,
    status: int = 200,
    **kwargs: Any,
) -> KeyrunesClient:
    """Build a client whose httpx transport is a mock returning ``payload``."""
    client = KeyrunesClient(base_url=BASE_URL, **kwargs)
    response = MagicMock()
    response.status_code = status
    response.json.return_value = payload if payload is not None else {}
    response.text = "body"
    transport = MagicMock()
    transport.request.return_value = response
    transport.headers = client._client.headers
    client._client = transport
    return client


def _sent(client: KeyrunesClient) -> Dict[str, Any]:
    """Return the kwargs of the last transport call."""
    return client._client.request.call_args.kwargs


class TestTransportArgumentPassthrough:
    """Every argument handed to ``_make_request`` must reach the transport."""

    @given(
        method=st.sampled_from(["GET", "POST", "PUT", "PATCH", "DELETE"]),
        segment=st.text(
            alphabet=st.characters(whitelist_categories=("Ll",)),
            min_size=1,
            max_size=10,
        ),
    )
    @PROPERTY_SETTINGS
    def test_http_method_reaches_the_transport_verbatim(
        self, method: str, segment: str
    ) -> None:
        client = _client_with_transport({"ok": True})
        client._make_request(method, f"/api/{segment}")
        assert _sent(client)["method"] == method
        client.close()

    def test_body_and_params_reach_the_transport(self) -> None:
        client = _client_with_transport({"ok": True})
        body = {"a": 1, "b": "two"}
        params = {"page": 3}
        client._make_request("POST", "/api/thing", data=body, params=params)
        sent = _sent(client)
        assert sent["json"] == body
        assert sent["params"] == params
        client.close()

    def test_auth_header_is_attached_only_when_requested(self) -> None:
        client = _client_with_transport({"ok": True})
        client.set_token("tok-123")

        client._make_request("GET", "/api/thing", use_auth=True)
        assert _sent(client)["headers"]["Authorization"] == "Bearer tok-123"

        client._make_request("GET", "/api/thing", use_auth=False)
        assert "Authorization" not in _sent(client)["headers"]
        client.close()

    def test_no_auth_header_without_a_token(self) -> None:
        client = _client_with_transport({"ok": True})
        client._make_request("GET", "/api/thing", use_auth=True)
        assert "Authorization" not in _sent(client)["headers"]
        client.close()

    def test_leading_x_in_endpoint_is_not_stripped(self) -> None:
        # ``endpoint.lstrip("/")`` must strip slashes only, never letters.
        client = _client_with_transport({"ok": True})
        client._make_request("GET", "/Xray")
        assert _sent(client)["url"] == f"{BASE_URL}/Xray"
        client.close()

    def test_trailing_x_in_base_url_is_not_stripped(self) -> None:
        # ``base_url.rstrip("/")`` must strip slashes only, never letters.
        client = KeyrunesClient(base_url="https://keyrunes.exampleX/")
        assert client.base_url == "https://keyrunes.exampleX"
        client.close()


class TestEndpointContract:
    """Each public operation must target its documented endpoint."""

    def test_login_posts_credentials_to_api_login(self) -> None:
        client = _client_with_transport({"token": JWT})
        client.login("john", "secret", namespace="tenant-a")
        sent = _sent(client)
        assert sent["method"] == "POST"
        assert sent["url"] == f"{BASE_URL}/api/login"
        assert sent["json"] == {
            "identity": "john",
            "password": "secret",
            "namespace": "tenant-a",
        }
        # Login must not send a stale Authorization header.
        assert "Authorization" not in sent["headers"]
        client.close()

    def test_login_defaults_the_namespace_to_public(self) -> None:
        client = _client_with_transport({"token": JWT})
        client.login("john", "secret")
        assert _sent(client)["json"]["namespace"] == "public"
        client.close()

    def test_login_stores_the_token_and_its_claims(self) -> None:
        client = _client_with_transport({"token": JWT})
        client.login("john", "secret")
        assert client._token == JWT
        assert client._token_data is not None
        assert client._token_data["sub"] == "user123"
        client.close()

    def test_register_user_posts_to_api_register(self) -> None:
        payload = {
            "user": {
                "id": "u1",
                "username": "john",
                "email": "john@example.com",
            }
        }
        client = _client_with_transport(payload)
        client.register_user(
            "john", "john@example.com", "password123", namespace="tenant-a"
        )
        sent = _sent(client)
        assert sent["method"] == "POST"
        assert sent["url"] == f"{BASE_URL}/api/register"
        assert sent["json"]["username"] == "john"
        assert sent["json"]["email"] == "john@example.com"
        assert sent["json"]["password"] == "password123"
        assert sent["json"]["namespace"] == "tenant-a"
        client.close()

    def test_register_admin_posts_the_admin_key(self) -> None:
        payload = {
            "user": {
                "id": "a1",
                "username": "root",
                "email": "root@example.com",
            }
        }
        client = _client_with_transport(payload)
        client.register_admin(
            "root", "root@example.com", "password123", "the-admin-key"
        )
        sent = _sent(client)
        # Admin registration reuses the public registration endpoint; the
        # admin key travels in the body, not in the path.
        assert sent["method"] == "POST"
        assert sent["url"] == f"{BASE_URL}/api/register"
        assert sent["json"]["admin_key"] == "the-admin-key"
        client.close()

    def test_get_user_targets_the_user_endpoint(self) -> None:
        payload = {
            "id": "other",
            "username": "jane",
            "email": "jane@example.com",
        }
        client = _client_with_transport(payload)
        client.set_token(JWT)
        client.get_user("other")
        sent = _sent(client)
        assert sent["method"] == "GET"
        assert sent["url"] == f"{BASE_URL}/api/users/other"
        client.close()

    def test_has_group_targets_the_membership_endpoint(self) -> None:
        # ``GroupCheck`` requires the full triple, not just the flag.
        client = _client_with_transport(
            {"user_id": "other", "group_id": "admins", "has_access": True}
        )
        client.set_token(JWT)
        assert client.has_group("other", "admins") is True
        sent = _sent(client)
        assert sent["method"] == "GET"
        assert sent["url"] == f"{BASE_URL}/api/users/other/groups/admins"
        client.close()

    def test_has_group_reports_a_denied_membership(self) -> None:
        client = _client_with_transport(
            {"user_id": "other", "group_id": "admins", "has_access": False}
        )
        client.set_token(JWT)
        assert client.has_group("other", "admins") is False
        client.close()


class TestTokenShortcutBranches:
    """Claims already in the JWT must be served without an HTTP round trip."""

    def test_get_user_for_self_is_answered_from_the_token(self) -> None:
        client = _client_with_transport({})
        client.set_token(JWT)
        user = client.get_user("user123")
        assert user.id == "user123"
        assert user.username == "john"
        assert user.groups == ["users"]
        client._client.request.assert_not_called()
        client.close()

    def test_get_current_user_is_answered_from_the_token(self) -> None:
        client = _client_with_transport({})
        client.set_token(JWT)
        me = client.get_current_user()
        assert me.id == "user123"
        assert me.email == "john@example.com"
        client._client.request.assert_not_called()
        client.close()

    def test_has_group_for_self_is_answered_from_the_token(self) -> None:
        client = _client_with_transport({})
        client.set_token(JWT)
        assert client.has_group("user123", "users") is True
        assert client.has_group("user123", "admins") is False
        client._client.request.assert_not_called()
        client.close()

    def test_get_user_groups_without_id_uses_the_current_user(self) -> None:
        client = _client_with_transport({})
        client.set_token(JWT)
        assert client.get_user_groups() == ["users"]
        client.close()


class TestUnauthenticatedGuards:
    """Operations that need a token must refuse before touching the network."""

    @pytest.mark.parametrize(
        "operation",
        [
            lambda c: c.get_user("u1"),
            lambda c: c.get_current_user(),
            lambda c: c.has_group("u1", "g1"),
        ],
    )
    def test_operations_refuse_without_a_token(self, operation: Any) -> None:
        client = _client_with_transport({})
        with pytest.raises(AuthenticationError):
            operation(client)
        client._client.request.assert_not_called()
        client.close()


class TestHeaderConfiguration:
    """Constructor-level headers must be installed on the httpx client."""

    def test_organization_key_argument_wins_over_the_environment(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("KEYRUNES_ORG_KEY", "from-env")
        client = KeyrunesClient(base_url=BASE_URL, organization_key="explicit")
        assert client.organization_key == "explicit"
        assert client._client.headers["X-Organization-Key"] == "explicit"
        client.close()

    def test_organization_key_falls_back_to_the_environment(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("KEYRUNES_ORG_KEY", "from-env")
        client = KeyrunesClient(base_url=BASE_URL)
        assert client.organization_key == "from-env"
        assert client._client.headers["X-Organization-Key"] == "from-env"
        client.close()

    def test_no_organization_header_when_unconfigured(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("KEYRUNES_ORG_KEY", raising=False)
        client = KeyrunesClient(base_url=BASE_URL)
        assert client.organization_key is None
        assert "X-Organization-Key" not in client._client.headers
        client.close()

    def test_timeout_is_forwarded_to_httpx(self) -> None:
        client = KeyrunesClient(base_url=BASE_URL, timeout=7)
        assert client.timeout == 7
        assert client._client.timeout.read == 7
        client.close()


class TestRegistrationDefaults:
    """Registration defaults and pass-through arguments.

    A mutation run showed these were unasserted: flipping the default
    namespace, dropping the extra attributes or dropping ``use_auth=False``
    all left the suite green.
    """

    REGISTER_RESPONSE = {
        "user": {
            "id": "u1",
            "username": "john",
            "email": "john@example.com",
        }
    }

    def test_register_user_defaults_the_namespace_to_public(self) -> None:
        client = _client_with_transport(self.REGISTER_RESPONSE)
        client.register_user("john", "john@example.com", "password123")
        assert _sent(client)["json"]["namespace"] == "public"
        client.close()

    def test_register_admin_defaults_the_namespace_to_public(self) -> None:
        client = _client_with_transport(self.REGISTER_RESPONSE)
        client.register_admin(
            "john", "john@example.com", "password123", "admin-key"
        )
        assert _sent(client)["json"]["namespace"] == "public"
        client.close()

    def test_register_user_forwards_extra_attributes(self) -> None:
        client = _client_with_transport(self.REGISTER_RESPONSE)
        client.register_user(
            "john",
            "john@example.com",
            "password123",
            department="Engineering",
            seniority=3,
        )
        attributes = _sent(client)["json"]["attributes"]
        assert attributes == {"department": "Engineering", "seniority": 3}
        client.close()

    def test_register_admin_forwards_extra_attributes(self) -> None:
        client = _client_with_transport(self.REGISTER_RESPONSE)
        client.register_admin(
            "john",
            "john@example.com",
            "password123",
            "admin-key",
            department="Security",
        )
        attributes = _sent(client)["json"]["attributes"]
        assert attributes == {"department": "Security"}
        client.close()

    def test_registration_never_sends_the_authorization_header(self) -> None:
        # Registration is an unauthenticated endpoint: a stale token must not
        # leak into the request.
        client = _client_with_transport(self.REGISTER_RESPONSE)
        client.set_token(JWT)

        client.register_user("john", "john@example.com", "password123")
        assert "Authorization" not in _sent(client)["headers"]

        client.register_admin(
            "john", "john@example.com", "password123", "admin-key"
        )
        assert "Authorization" not in _sent(client)["headers"]
        client.close()

    def test_login_never_sends_the_authorization_header(self) -> None:
        client = _client_with_transport({"token": JWT})
        client.set_token("stale-token")
        client.login("john", "secret")
        assert "Authorization" not in _sent(client)["headers"]
        client.close()

    @pytest.mark.parametrize(
        "call",
        [
            lambda c: c.register_user("john", "john@example.com", "pw123456"),
            lambda c: c.register_admin(
                "john", "john@example.com", "pw123456", "key"
            ),
        ],
    )
    def test_registration_rejects_a_response_without_a_user(
        self, call: Any
    ) -> None:
        from keyrunes_sdk.exceptions import NetworkError

        client = _client_with_transport({"unexpected": True})
        with pytest.raises(NetworkError):
            call(client)
        client.close()


class TestIdentityFieldsSurviveNormalization:
    """Keyrunes answers with more identity than ``User`` used to carry.

    A consumer that keys its own records off the JWT ``sub`` needs ``user_id``,
    which is a different value from ``id`` (the external UUID). Losing it
    silently re-keys every mirrored record, so it is pinned here.
    """

    #: What the Keyrunes server actually returns for a user.
    SERVER_USER = {
        "id": "0b8f6e9c-2c4c-4f6f-9c0e-1f2a3b4c5d6e",
        "user_id": 42,
        "email": "john@example.com",
        "username": "john",
        "groups": ["users"],
        "namespace": "public",
        "organization_id": 7,
        "first_login": True,
    }

    def test_user_id_is_kept_apart_from_the_external_id(self):
        client = _client_with_transport(self.SERVER_USER)
        client.set_token(JWT)

        user = client.get_user("someone-else")

        assert user.id == self.SERVER_USER["id"]
        assert user.user_id == "42"

    def test_namespace_and_organization_survive(self):
        client = _client_with_transport(self.SERVER_USER)
        client.set_token(JWT)

        user = client.get_user("someone-else")

        assert user.namespace == "public"
        assert user.organization_id == 7
        assert user.first_login is True

    def test_a_payload_without_the_extra_fields_still_parses(self):
        client = _client_with_transport(
            {
                "id": "abc",
                "username": "u",
                "email": "u@example.com",
                "groups": [],
            }
        )
        client.set_token(JWT)

        user = client.get_user("someone-else")

        assert user.user_id is None
        assert user.namespace is None
        assert user.organization_id is None
        assert user.first_login is False

    def test_login_carries_the_password_change_flag(self):
        client = _client_with_transport(
            {
                "token": JWT,
                "requires_password_change": True,
                "user": self.SERVER_USER,
            }
        )

        token = client.login("john", "password123")

        assert token.requires_password_change is True
        assert token.user is not None
        assert token.user.user_id == "42"

    def test_the_password_change_flag_defaults_to_false(self):
        client = _client_with_transport(
            {"token": JWT, "user": self.SERVER_USER}
        )

        assert (
            client.login("john", "password123").requires_password_change
            is False
        )


class TestRefreshToken:
    """``POST /api/refresh-token`` exchanges a live token for a fresh one."""

    def test_posts_the_current_token_to_the_refresh_endpoint(self):
        client = _client_with_transport({"token": JWT})
        client.set_token(JWT)

        client.refresh_token()

        sent = _sent(client)
        assert sent["method"] == "POST"
        assert sent["url"] == f"{BASE_URL}/api/refresh-token"
        assert sent["json"] == {"token": JWT}

    def test_an_explicit_token_wins_over_the_stored_one(self):
        client = _client_with_transport({"token": JWT})
        client.set_token("stored-token")

        client.refresh_token(JWT)

        assert _sent(client)["json"] == {"token": JWT}

    def test_the_refreshed_token_is_adopted_by_the_client(self):
        client = _client_with_transport({"token": JWT})
        client.set_token("stale")

        refreshed = client.refresh_token("stale")

        assert refreshed.access_token == JWT
        assert client._token == JWT

    def test_refreshing_without_a_token_raises_rather_than_calling_the_server(
        self,
    ):
        client = _client_with_transport({"token": JWT})

        with pytest.raises(InvalidTokenError):
            client.refresh_token()

        client._client.request.assert_not_called()

    def test_a_rejected_token_surfaces_as_an_authentication_error(self):
        client = _client_with_transport({"error": "expired"}, status=401)

        with pytest.raises(AuthenticationError):
            client.refresh_token("expired-token")


class TestCurrentUserEndpoint:
    """``get_current_user`` and the claims shortcut it can take."""

    SERVER_USER = {
        "id": "ext-1",
        "user_id": 42,
        "email": "john@example.com",
        "username": "john",
        "groups": ["users"],
    }

    def test_asks_the_server_at_api_me(self):
        # The Keyrunes router exposes /api/me; /api/users/me does not exist and
        # answered 404 against a real server.
        client = _client_with_transport(self.SERVER_USER)
        client._token = JWT
        client._token_data = None

        client.get_current_user()

        sent = _sent(client)
        assert sent["method"] == "GET"
        assert sent["url"] == f"{BASE_URL}/api/me"

    def test_the_claims_shortcut_skips_the_server(self):
        client = _client_with_transport(self.SERVER_USER)
        client.set_token(JWT)

        user = client.get_current_user()

        assert user.username == "john"
        client._client.request.assert_not_called()

    def test_force_refresh_always_asks_the_server(self):
        # The shortcut reads a token the SDK never verified, so a caller
        # deciding whether the token is still good must be able to demand the
        # round trip.
        client = _client_with_transport(self.SERVER_USER)
        client.set_token(JWT)

        user = client.get_current_user(force_refresh=True)

        assert _sent(client)["url"] == f"{BASE_URL}/api/me"
        assert user.user_id == "42"

    def test_force_refresh_surfaces_a_rejected_token(self):
        client = _client_with_transport({"error": "nope"}, status=401)
        client.set_token(JWT)

        with pytest.raises(AuthenticationError):
            client.get_current_user(force_refresh=True)

    def test_an_unauthenticated_client_never_calls_the_server(self):
        client = _client_with_transport(self.SERVER_USER)

        with pytest.raises(AuthenticationError):
            client.get_current_user(force_refresh=True)

        client._client.request.assert_not_called()


class TestRegistrationResponseShape:
    """``POST /api/register`` answers with the bare user object.

    The Keyrunes handler returns ``Json(auth_response.user)`` — there is no
    ``{"user": ...}`` envelope — so requiring one made every real registration
    fail with "Unexpected response format".
    """

    BARE_USER = {
        "id": "ext-1",
        "user_id": 7,
        "email": "new@example.com",
        "username": "new",
        "groups": ["users"],
    }

    def test_a_bare_user_object_is_accepted(self):
        client = _client_with_transport(self.BARE_USER)

        user = client.register_user("new", "new@example.com", "password123")

        assert user.username == "new"
        assert user.user_id == "7"

    def test_a_wrapped_user_object_is_still_accepted(self):
        client = _client_with_transport({"user": self.BARE_USER})

        assert (
            client.register_user("new", "new@example.com", "pw123456").user_id
            == "7"
        )

    def test_a_response_with_no_identifier_is_rejected(self):
        client = _client_with_transport({"message": "created"})

        with pytest.raises(NetworkError):
            client.register_user("new", "new@example.com", "password123")

    def test_admin_registration_accepts_a_bare_user_object(self):
        client = _client_with_transport(self.BARE_USER)

        admin = client.register_admin(
            "new", "new@example.com", "password123", admin_key="k"
        )

        assert admin.user_id == "7"


class TestRegistrationGroupPlacement:
    """``group`` is a top-level field on the server's RegisterApi payload."""

    BARE_USER = {
        "id": "ext-1",
        "user_id": 7,
        "email": "n@example.com",
        "username": "n",
    }

    def test_group_is_sent_top_level_not_nested_in_attributes(self):
        client = _client_with_transport(self.BARE_USER)

        client.register_user(
            "newbie", "n@example.com", "password123", group="instructor"
        )

        body = _sent(client)["json"]
        assert body["group"] == "instructor"
        assert "group" not in body["attributes"]

    def test_no_group_key_is_sent_when_none_is_given(self):
        client = _client_with_transport(self.BARE_USER)

        client.register_user("newbie", "n@example.com", "password123")

        assert "group" not in _sent(client)["json"]

    def test_other_keyword_attributes_still_nest_under_attributes(self):
        client = _client_with_transport(self.BARE_USER)

        client.register_user(
            "newbie", "n@example.com", "password123", department="Engineering"
        )

        body = _sent(client)["json"]
        assert body["attributes"] == {"department": "Engineering"}


class TestErrorStatusIsCarried:
    """A caller must be able to tell a refused request from an outage."""

    @pytest.mark.parametrize("status", [400, 409, 422, 500, 502, 503])
    def test_the_response_status_reaches_the_caller(self, status):
        client = _client_with_transport({"error": "nope"}, status=status)

        with pytest.raises(NetworkError) as excinfo:
            client.login("john", "password123")

        assert excinfo.value.status_code == status

    def test_a_transport_failure_carries_no_status(self):
        import httpx

        client = _client_with_transport({})
        client._client.request.side_effect = httpx.ConnectError("down")

        with pytest.raises(NetworkError) as excinfo:
            client.login("john", "password123")

        # No response ever arrived, so there is no status to report.
        assert excinfo.value.status_code is None

    def test_the_message_still_reads_normally(self):
        client = _client_with_transport({"error": "duplicate"}, status=409)

        with pytest.raises(NetworkError) as excinfo:
            client.login("john", "password123")

        assert "duplicate" in str(excinfo.value)
