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
