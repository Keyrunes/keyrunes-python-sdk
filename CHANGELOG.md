# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

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
