# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

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
