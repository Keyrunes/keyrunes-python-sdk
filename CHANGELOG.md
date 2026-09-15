# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [0.4.0] - 2026-09-15

### Added

- `KeyrunesClient.change_password(current_password, new_password)`, wrapping
  `POST /api/user/change-password`. The server has served this endpoint all
  along; the SDK exposed `login`, `refresh_token`, `register_user` and the group
  queries, and not this one. Anyone who needed it built the HTTP call by hand —
  which is what happened downstream, after first concluding from the SDK's
  surface that the operation did not exist at all.

  Three details the endpoint carries, and each one bites if read wrong:

  - it lives at `/api/user/change-password`, **not** `/api/change-password` —
    the router registers the first, and the handler behind the second is dead
    code marked `#[allow(dead_code)]`, so pointing at it answers 404;
  - it answers errors as **plain text** (`e.to_string()`), not JSON, and with
    status **400** rather than 401 — so this client raises `NetworkError`, the
    same class it already uses for every non-401/403/404 status, and preserves
    the server's own wording, because "invalid current password" and "password
    too short" call for opposite fixes;
  - changing the password clears the account's `first_login` flag server-side,
    which is what `requires_password_change` reports at login. There is no
    second call to make.

  Without a token the client refuses before sending: the server decides whose
  password it is from the token, and nothing in the body chooses that.

### Fixed

- A malformed `groups` field in a server response no longer crashes the client.
  `get_current_user` and `check_user` called `list(data["groups"])` on whatever
  came back; a JSON `true`, a number, or `null` raised `TypeError: 'bool' object
  is not iterable` out of the SDK, from a line that reads like a safe coercion.
  Anything that is not a JSON array is now read as no groups. Found by the fuzz
  suite, and it predates this release — `git stash` confirmed it on the previous
  tag.

### Security

- `pyjwt` 2.10.1 → 2.14.0 and `idna` 3.11 → 3.19 in the lockfile. Both are
  runtime dependencies (`idna` arrives through `httpx`), and OSV reports known
  advisories against the pinned versions — nine for `pyjwt`, four of them high.
  The declared constraint was already `^2.9.0`, so this is a lockfile refresh
  with no API change; the 194 tests pass unchanged.

### Removed

- `towncrier` left the dev dependencies. It was declared and never configured:
  no `[tool.towncrier]` section, no `newsfragments/` directory, and this
  changelog was written by hand. A tool nobody runs still gets installed,
  resolved, and audited on every environment build.

## [0.3.1] - 2026-09-04

### Fixed

- `mutmut` is no longer a runtime dependency. It was declared in
  `[tool.poetry.dependencies]` instead of the dev group, so installing this SDK
  pulled a mutation-testing tool and its whole tree — `libcst`, `textual`,
  `rich`, `setproctitle`, `pyyaml-ft`, `markdown-it-py`, `mdit-py-plugins`,
  `mdurl`, `linkify-it-py`, `sortedcontainers` — into every consumer, including
  production images. Affected 0.2.0 and 0.3.0; nothing in the library imported
  it, so upgrading only removes packages.

## [0.3.0] - 2026-09-03

### Added

- `User.user_id`, carrying the internal identifier Keyrunes puts in the JWT
  `sub` claim. It is a different value from `User.id` (the external UUID), and
  a consumer that keys its own records off `sub` needs it; before this release
  it was discarded during normalization and could only be recovered by
  re-parsing the token.
- `User.namespace`, `User.organization_id` and `User.first_login`, all of which
  the server returns and normalization used to drop.
- `Token.requires_password_change`, so a login that must be followed by a
  password change can be detected without reading the raw response.
- `KeyrunesClient.refresh_token()`, wrapping `POST /api/refresh-token`. It
  accepts an explicit token or falls back to the client's current one, raises
  `InvalidTokenError` when neither is available, and adopts the refreshed
  token the way `login()` does.
- `get_current_user(force_refresh=True)`, which always asks the server. The
  claims shortcut reads a token the SDK never verified, so it cannot answer
  "is this token still accepted"; a caller validating a token needs the round
  trip.
- `KeyrunesError.status_code`, carrying the HTTP status when the error came
  from a response rather than from the transport. Without it a caller cannot
  tell "the server refused this request" (4xx) from "the server or the network
  failed" (5xx, or no response at all), and both are raised as `NetworkError`.
- `register_user(group=...)`, sent as a top-level field.
- A `py.typed` marker (PEP 561). The package was already fully typed, but
  without the marker a consumer running mypy saw every SDK import as
  untyped.

### Fixed

- `get_current_user()` asked for `/api/users/me`, which the Keyrunes router
  does not expose — the real route is `/api/me`, so the call answered 404
  against a live server whenever the claims shortcut did not cover it. The
  endpoint is now a named constant, `ENDPOINT_ME`.
- `register_user()` and `register_admin()` required the response to be
  `{"user": {...}}`, but `POST /api/register` answers with the bare user
  object. Every registration against a real server failed with "Unexpected
  response format". Both shapes are now accepted.
- Extra keyword arguments to `register_user()` were nested under `attributes`,
  so a `group` never reached the server, which reads it as a top-level field.
  `group` is now an explicit parameter placed at the top level; other keyword
  attributes keep nesting under `attributes`.

### Testing

- Test count raised from 159 to 189.

### Notes

- Every added field is optional with a backwards-compatible default, and
  `User.id` keeps its existing precedence (`id` → `user_id` → `external_id`).
  Code written against 0.2.0 keeps working unchanged.

## [0.2.0] - 2026-09-03

### Added

- Property-based test suite (`tests/test_property_based.py`, 24 tests) built on
  Hypothesis, covering base URL normalization, `_normalize_user` id precedence
  and `is_admin` derivation, JWT claim parsing, request URL construction, HTTP
  status to exception mapping, and model validation bounds.
- Input fuzzing ("spider") suite (`tests/test_fuzz.py`, 19 tests) that crawls the
  public surface with hostile payloads and asserts that only `KeyrunesError` and
  pydantic `ValidationError` ever escape, and that nothing panics or leaks a raw
  `ValueError`/`TypeError`.
- Request contract suite (`tests/test_request_contract.py`, 33 tests) that mocks
  only the httpx transport, so the method, URL, headers and JSON body actually
  put on the wire are asserted for every endpoint.
- Hypothesis profiles in `tests/conftest.py` (`fast`, `dev`, `ci`) selected via
  the `HYPOTHESIS_PROFILE` environment variable. `fast` is derandomized and
  database-free so mutation runs judge every mutant against identical examples.
- `[tool.mutmut]` configuration in `pyproject.toml` for mutation testing.
- `hypothesis` added as a development dependency.

### Fixed

- A 2xx response carrying a non-JSON body raised a raw `ValueError` out of
  `KeyrunesClient._make_request`. It is now wrapped in `NetworkError`, so the
  documented exception contract holds for malformed responses.

### Changed

- Extracted the duplicated "build a `User` from JWT claims" block into
  `KeyrunesClient._user_from_token_claims()`.

### Removed

- Unreachable `except UserNotFoundError` fallbacks in `get_user`,
  `get_current_user` and `has_group`. Each re-tested a condition that had
  already forced an early return, so a 404 from the server was being swallowed
  instead of propagated.

### Testing

- Test count raised from 83 to 159.
- Mutation score (mutmut) raised from 44% (294/669 mutants killed) to 72%
  (387/537). The remaining survivors are predominantly equivalent mutants that
  only alter error message prose.

## [0.1.0] - 2025-12-03

### Adicionado

#### Funcionalidades Core
- Cliente `KeyrunesClient` completo para interação com Keyrunes API
- Autenticação com login de usuário e admin
- Registro de usuário e admin com validação
- Verificação de pertencimento a grupos
- Obtenção de informações de usuários

#### Decorators
- `@require_group()` - Decorator para verificar grupos de usuários
- `@require_admin()` - Decorator para verificar privilégios de admin
- Suporte para múltiplos grupos (ANY ou ALL)
- Sistema de client global para uso sem passar client explicitamente

#### Modelos Pydantic
- `User` - Modelo de usuário com validação
- `Token` - Modelo de token JWT
- `Group` - Modelo de grupo
- `UserRegistration` - Dados de registro de usuário
- `AdminRegistration` - Dados de registro de admin
- `LoginCredentials` - Credenciais de login
- `GroupCheck` - Resultado de verificação de grupo

#### Exceções Customizadas
- `KeyrunesError` - Exceção base
- `AuthenticationError` - Erro de autenticação
- `AuthorizationError` - Erro de autorização
- `GroupNotFoundError` - Grupo não encontrado
- `UserNotFoundError` - Usuário não encontrado
- `InvalidTokenError` - Token inválido
- `NetworkError` - Erro de rede

#### Sistema de Configuração Global
- `configure()` - Configura client global
- `get_global_client()` - Obtém client global
- `clear_global_client()` - Limpa client global
- Thread-safe com Lock

#### Desenvolvimento e Testes
- Docker Compose completo com Keyrunes, PostgreSQL e Redis
- 78 testes com 99% de cobertura
- Testes usando pytest, factory-boy e faker
- Exemplos práticos de uso
- Makefile com comandos úteis
- Configuração completa de CI/CD

#### Documentação
- README.md completo com exemplos
- TESTING.md com guia de testes
- Docstrings em todas as funções
- Type hints completos
- Exemplos práticos em `examples/`

### Detalhes Técnicos

- Python 3.8.1+ compatível
- Gerenciamento com Poetry
- Validação com Pydantic 2.0
- Type hints completos
- Thread-safe
- Context manager support

### Testes

- 78 testes implementados
- 99% de cobertura de código
- Testes unitários e de integração
- Factories com factory-boy
- Dados fake com Faker

### Ferramentas de Desenvolvimento

- Black para formatação
- isort para organização de imports
- flake8 para linting
- mypy para type checking
- pytest para testes

## [Unreleased]

### Planejado

- Suporte para refresh token automático
- Cache de verificações de grupo
- Suporte para OIDC
- Integração com FastAPI
- Integração com Flask
- Integração com Django
- Mais exemplos práticos
- Documentação com Sphinx
- Publicação no PyPI

---

Para mais detalhes sobre cada versão, veja os [releases no GitHub](https://github.com/jonatasoli/keyurnes-sdk-python-dark/releases).
