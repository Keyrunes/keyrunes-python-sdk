0.3.0 (2026-09-03)
==================

Features
--------

- Keep ``user_id``, ``namespace``, ``organization_id`` and ``first_login`` on
  ``User`` instead of discarding them during normalization
- Carry ``requires_password_change`` on ``Token``
- Add ``KeyrunesClient.refresh_token()`` for ``POST /api/refresh-token``
- Add ``get_current_user(force_refresh=True)`` for callers that must validate a
  token against the server rather than trust its unverified claims


- Add ``KeyrunesError.status_code`` so a refused request can be told apart from
  an outage
- Add an explicit ``group`` parameter to ``register_user``


Bugfixes
--------

- Ask ``/api/me`` instead of the non-existent ``/api/users/me`` in
  ``get_current_user``
- Accept the bare user object ``POST /api/register`` actually returns, instead
  of requiring a ``{"user": ...}`` envelope that made every registration fail
- Send ``group`` as a top-level registration field instead of burying it in
  ``attributes``, where the server never looked


0.2.0 (2026-09-03)
==================

Bugfixes
--------

- Wrap a non-JSON body on a 2xx response in ``NetworkError`` instead of letting a
  raw ``ValueError`` escape ``_make_request``
- Propagate a server 404 from ``get_user``, ``get_current_user`` and
  ``has_group`` instead of swallowing it in an unreachable fallback branch


Misc
----

- Add Hypothesis property-based, input fuzzing and request contract test suites
  (83 -> 159 tests)
- Add mutmut configuration and raise the mutation score from 44% to 72%


0.1.0 (2026-01-03)
==================

Features
--------

- Add organization key feature


Misc
----

- Add pre-commit with tests, lint and safety


0.0.1 (2025-12-08)
==================

Features
--------

- Add Login and Register routes
- Add check user and admin
- Add get current user
