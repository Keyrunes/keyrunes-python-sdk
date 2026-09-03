"""Fuzz ("spider") tests for the Keyrunes SDK.

Where ``test_property_based.py`` asserts algebraic invariants over *valid*
inputs, this module crawls the *hostile* input space: arbitrary JSON payloads,
malformed tokens, unexpected status codes and broken response bodies. The
contract under test is a robustness one — the SDK may reject an input, but it
must do so through its own documented exception hierarchy and must never leak
a raw ``ValueError``/``KeyError``/``AttributeError`` from its internals.
"""

from typing import Any, Dict
from unittest.mock import MagicMock

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from keyrunes_sdk.client import KeyrunesClient
from keyrunes_sdk.decorators import require_admin, require_group
from keyrunes_sdk.exceptions import (
    AuthenticationError,
    AuthorizationError,
    KeyrunesError,
    NetworkError,
    UserNotFoundError,
)

FUZZ_SETTINGS = settings(
    deadline=None,
    suppress_health_check=[
        HealthCheck.function_scoped_fixture,
        HealthCheck.too_slow,
        # mutmut re-runs the suite in a single process, which trips this.
        HealthCheck.differing_executors,
    ],
)

# Exceptions the SDK is allowed to surface. A ``ValidationError`` is pydantic
# rejecting a payload that violates the declared model, which is a deliberate
# part of the contract; anything outside this tuple is a leak.
ALLOWED = (KeyrunesError, ValidationError)

# Arbitrary JSON values, including deeply nested ones.
json_values = st.recursive(
    st.none()
    | st.booleans()
    | st.integers()
    | st.floats(allow_nan=False, allow_infinity=False)
    | st.text(max_size=30),
    lambda children: st.lists(children, max_size=4)
    | st.dictionaries(st.text(max_size=12), children, max_size=4),
    max_leaves=12,
)

json_objects = st.dictionaries(st.text(max_size=16), json_values, max_size=8)


def _client() -> KeyrunesClient:
    return KeyrunesClient(base_url="https://keyrunes.example.com")


class TestNormalizeUserFuzz:
    """``_normalize_user`` must never leak a non-SDK exception."""

    @given(payload=json_objects)
    @FUZZ_SETTINGS
    def test_arbitrary_payloads_never_leak_internal_errors(
        self, payload: Dict[str, Any]
    ) -> None:
        try:
            user = KeyrunesClient._normalize_user(payload)
        except ALLOWED:
            return
        assert isinstance(user.id, str)
        assert isinstance(user.groups, list)
        assert isinstance(user.is_admin, bool)

    @given(payload=json_objects)
    @FUZZ_SETTINGS
    def test_empty_payload_is_rejected_as_network_error(
        self, payload: Dict[str, Any]
    ) -> None:
        # Any falsy payload takes the explicit guard clause.
        with pytest.raises(NetworkError):
            KeyrunesClient._normalize_user({})

    @given(groups=st.lists(json_values, max_size=6), email=st.emails())
    @FUZZ_SETTINGS
    def test_non_string_group_entries_do_not_crash_admin_detection(
        self, groups: list, email: str
    ) -> None:
        payload = {
            "id": "u1",
            "username": "u",
            "email": email,
            "groups": groups,
        }
        try:
            user = KeyrunesClient._normalize_user(payload)
        except ALLOWED:
            return
        assert isinstance(user.is_admin, bool)


class TestTokenParsingFuzz:
    """``_parse_token_response`` must never leak a non-SDK exception."""

    @given(payload=json_objects)
    @FUZZ_SETTINGS
    def test_arbitrary_payloads_never_leak_internal_errors(
        self, payload: Dict[str, Any]
    ) -> None:
        client = _client()
        try:
            token = client._parse_token_response(dict(payload))
        except ALLOWED:
            return
        finally:
            client.close()
        assert isinstance(token.access_token, str)

    @given(user_payload=json_values, token=st.text(min_size=1, max_size=40))
    @FUZZ_SETTINGS
    def test_hostile_embedded_user_is_contained(
        self, user_payload: Any, token: str
    ) -> None:
        client = _client()
        try:
            client._parse_token_response({"token": token, "user": user_payload})
        except ALLOWED:
            pass
        finally:
            client.close()


class TestSetTokenFuzz:
    """``set_token`` swallows every decoding failure by design."""

    @given(token=st.text(max_size=200))
    @FUZZ_SETTINGS
    def test_arbitrary_token_strings_never_raise(self, token: str) -> None:
        client = _client()
        client.set_token(token)
        assert client._token == token
        client.close()

    @given(
        parts=st.lists(
            st.text(
                alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd")),
                max_size=20,
            ),
            min_size=0,
            max_size=6,
        )
    )
    @FUZZ_SETTINGS
    def test_jwt_shaped_garbage_leaves_token_data_absent_or_dict(
        self, parts: list
    ) -> None:
        client = _client()
        client.set_token(".".join(parts))
        assert client._token_data is None or isinstance(
            client._token_data, dict
        )
        client.close()

    @given(token=st.text(max_size=80))
    @FUZZ_SETTINGS
    def test_clear_token_always_restores_the_unauthenticated_state(
        self, token: str
    ) -> None:
        client = _client()
        client.set_token(token)
        client.clear_token()
        assert client._token is None
        assert client._token_data is None
        client.close()


class TestTransportFuzz:
    """Hostile HTTP responses must be funnelled into SDK exceptions."""

    @given(
        status=st.integers(min_value=100, max_value=599),
        body=json_objects,
    )
    @FUZZ_SETTINGS
    def test_any_status_and_body_yields_dict_or_sdk_error(
        self, status: int, body: Dict[str, Any]
    ) -> None:
        client = _client()
        response = MagicMock()
        response.status_code = status
        response.json.return_value = body
        response.text = "body"
        client._client = MagicMock()
        client._client.request.return_value = response

        try:
            result = client._make_request("GET", "/api/fuzz")
        except ALLOWED:
            return
        finally:
            client.close()
        assert result == body

    @given(status=st.integers(min_value=100, max_value=599))
    @FUZZ_SETTINGS
    def test_non_json_body_is_reported_as_network_error(
        self, status: int
    ) -> None:
        client = _client()
        response = MagicMock()
        response.status_code = status
        response.json.side_effect = ValueError("Expecting value")
        response.text = "<html>gateway timeout</html>"
        client._client = MagicMock()
        client._client.request.return_value = response

        with pytest.raises(KeyrunesError):
            client._make_request("GET", "/api/fuzz")
        client.close()

    @given(
        status=st.sampled_from([401, 403, 404]),
        body=json_objects,
    )
    @FUZZ_SETTINGS
    def test_auth_statuses_keep_their_exception_type_under_any_body(
        self, status: int, body: Dict[str, Any]
    ) -> None:
        client = _client()
        response = MagicMock()
        response.status_code = status
        response.json.return_value = body
        response.text = "body"
        client._client = MagicMock()
        client._client.request.return_value = response

        expected = {
            401: AuthenticationError,
            403: AuthorizationError,
            404: UserNotFoundError,
        }[status]
        with pytest.raises(expected):
            client._make_request("GET", "/api/fuzz")
        client.close()

    @given(
        endpoint=st.text(max_size=60),
        method=st.sampled_from(["GET", "POST", "PUT", "PATCH", "DELETE"]),
    )
    @FUZZ_SETTINGS
    def test_arbitrary_endpoints_produce_absolute_urls(
        self, endpoint: str, method: str
    ) -> None:
        client = _client()
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {}
        client._client = MagicMock()
        client._client.request.return_value = response

        try:
            client._make_request(method, endpoint)
        except ALLOWED:
            client.close()
            return
        url = client._client.request.call_args.kwargs["url"]
        assert url.startswith("http://") or url.startswith("https://")
        client.close()


class TestDecoratorFuzz:
    """Decorators must not be tricked into skipping their check."""

    @given(
        groups=st.lists(st.text(max_size=20), min_size=1, max_size=4),
        user_id=st.text(min_size=1, max_size=20),
    )
    @FUZZ_SETTINGS
    def test_require_group_denies_when_no_group_matches(
        self, groups: list, user_id: str
    ) -> None:
        client = MagicMock(spec=KeyrunesClient)
        client.has_group.return_value = False

        @require_group(*groups, client=client)
        def protected(user_id: str) -> str:
            return "executed"

        with pytest.raises(AuthorizationError):
            protected(user_id=user_id)

    @given(
        groups=st.lists(st.text(max_size=20), min_size=1, max_size=4),
        user_id=st.text(min_size=1, max_size=20),
    )
    @FUZZ_SETTINGS
    def test_require_group_allows_when_every_group_matches(
        self, groups: list, user_id: str
    ) -> None:
        client = MagicMock(spec=KeyrunesClient)
        client.has_group.return_value = True

        @require_group(*groups, client=client, all_groups=True)
        def protected(user_id: str) -> str:
            return "executed"

        assert protected(user_id=user_id) == "executed"

    @given(
        index=st.integers(min_value=0, max_value=3),
        user_id=st.text(min_size=1, max_size=20),
    )
    @FUZZ_SETTINGS
    def test_all_groups_denies_if_any_single_group_is_missing(
        self, index: int, user_id: str
    ) -> None:
        groups = ["g0", "g1", "g2", "g3"]
        client = MagicMock(spec=KeyrunesClient)
        client.has_group.side_effect = lambda _uid, gid: gid != groups[index]

        @require_group(*groups, client=client, all_groups=True)
        def protected(user_id: str) -> str:
            return "executed"

        with pytest.raises(AuthorizationError):
            protected(user_id=user_id)

    @given(
        index=st.integers(min_value=0, max_value=3),
        user_id=st.text(min_size=1, max_size=20),
    )
    @FUZZ_SETTINGS
    def test_any_group_allows_if_exactly_one_group_matches(
        self, index: int, user_id: str
    ) -> None:
        groups = ["g0", "g1", "g2", "g3"]
        client = MagicMock(spec=KeyrunesClient)
        client.has_group.side_effect = lambda _uid, gid: gid == groups[index]

        @require_group(*groups, client=client)
        def protected(user_id: str) -> str:
            return "executed"

        assert protected(user_id=user_id) == "executed"

    @given(user_id=st.text(min_size=1, max_size=20), is_admin=st.booleans())
    @FUZZ_SETTINGS
    def test_require_admin_follows_the_user_admin_flag(
        self, user_id: str, is_admin: bool
    ) -> None:
        client = MagicMock(spec=KeyrunesClient)
        client._token_data = None
        client.get_user.return_value = MagicMock(is_admin=is_admin)

        @require_admin(client=client)
        def protected(user_id: str) -> str:
            return "executed"

        if is_admin:
            assert protected(user_id=user_id) == "executed"
        else:
            with pytest.raises(AuthorizationError):
                protected(user_id=user_id)


class TestConstructionFuzz:
    """Client construction must not explode on odd but plausible inputs."""

    @given(
        base_url=st.text(max_size=60),
        timeout=st.integers(min_value=1, max_value=600),
    )
    @FUZZ_SETTINGS
    def test_arbitrary_base_urls_are_accepted_and_normalized(
        self, base_url: str, timeout: int
    ) -> None:
        try:
            client = KeyrunesClient(base_url=base_url, timeout=timeout)
        except ALLOWED:
            return
        assert not client.base_url.endswith("/")
        assert client.timeout == timeout
        client.close()

    @given(
        api_key=st.text(
            alphabet=st.characters(min_codepoint=33, max_codepoint=126),
            max_size=40,
        )
    )
    @FUZZ_SETTINGS
    def test_api_key_is_sent_as_a_header_when_truthy(
        self, api_key: str
    ) -> None:
        client = KeyrunesClient(
            base_url="https://keyrunes.example.com", api_key=api_key
        )
        if api_key:
            assert client._client.headers["X-API-Key"] == api_key
        else:
            assert "X-API-Key" not in client._client.headers
        client.close()
