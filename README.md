# Keyrunes SDK Python Client

[![Tests](https://github.com/Keyrunes/keyrunes-python-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/Keyrunes/keyrunes-python-sdk/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/Keyrunes/keyrunes-python-sdk/branch/main/graph/badge.svg)](https://codecov.io/gh/Keyrunes/keyrunes-python-sdk)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Python SDK for integration with the [Keyrunes Authorization System](https://github.com/Keyrunes/keyrunes), a modern high-performance authorization system built in Rust.

## Features

- Complete Authentication: Login, user and admin registration
- Group Verification: Check group membership
- Decorators: Ready-to-use authorization decorators (`@require_group`, `@require_admin`)
- Type Hints: Fully typed with mypy support
- Pydantic Models: Automatic data validation

## Installation

### Using Poetry (recommended)

```bash
poetry add keyrunes-sdk
```

### Using pip

```bash
pip install keyrunes-sdk
```

## Testing Examples Locally

1. Start local environment (Keyrunes + Postgres):
   ```bash
   docker-compose up -d
   ```
2. Verify service health (API on port 3000):
   ```bash
   curl http://localhost:3000/api/health
   ```
3. Run examples (use `KEYRUNES_BASE_URL` if you need to adjust the URL):
   ```bash
   KEYRUNES_BASE_URL=http://localhost:3000 poetry run python examples/test_local.py
   poetry run python examples/basic_usage.py
   poetry run python examples/global_client_usage.py
   ```
   > Tip: if your shell has an alias for `poetry`, use `\poetry` to bypass it.

## Tests and Coverage

- Run tests (uses pytest addopts already configured with coverage):
  ```bash
  poetry run task test
  ```
- Run tests and generate explicit coverage:
  ```bash
  poetry run task cov
  ```

## Ready-to-use Objects for Testing Login/Registration

Use `examples/test_objects.py` to generate unique payloads when testing manually and see usage examples:

### Available Functions

#### `user_registration_payload(suffix: str | None = None, password: str | None = None) -> dict`
Generates a dictionary with user registration data. Each call generates a unique suffix (UUID) and a random password to avoid conflicts.

**Parameters:**
- `suffix` (optional): Custom suffix. If not provided, generates a random UUID.
- `password` (optional): Custom password. If not provided, generates a secure random password (12 characters).

**Returns:** Dictionary with `username`, `email`, `password`, `department`, `role`.

**Example:**
```python
from examples.test_objects import user_registration_payload

user_data = user_registration_payload()
# {'username': 'user_a1b2c3', 'email': 'user_a1b2c3@example.com', 'password': 'random_generated_password', ...}
```

#### `admin_registration_payload(suffix: str | None = None, admin_key: str | None = None, password: str | None = None) -> dict`
Generates a dictionary with admin registration data. Uses `ADMIN_KEY` from environment if available and generates random password.

**Parameters:**
- `suffix` (optional): Custom suffix.
- `admin_key` (optional): Admin key. If not provided, uses `ADMIN_KEY` from environment or default value.
- `password` (optional): Custom password. If not provided, generates a secure random password (12 characters).

**Returns:** Dictionary with `username`, `email`, `password`, `admin_key`.

**Example:**
```python
from examples.test_objects import admin_registration_payload

admin_data = admin_registration_payload()
# {'username': 'admin_x9y8z7', 'email': 'admin_x9y8z7@example.com', 'password': 'random_generated_password', ...}
```

#### `login_payload(email: str, password: str) -> dict`
Generates a dictionary with login credentials in the format expected by the API.

**Parameters:**
- `email`: User email for login.
- `password`: User password (required).

**Returns:** Dictionary with `identity` (email) and `password`.

**Example:**
```python
from examples.test_objects import login_payload, user_registration_payload

user_data = user_registration_payload()
login_data = login_payload(email=user_data["email"], password=user_data["password"])
# {'identity': 'user_a1b2c3@example.com', 'password': 'random_generated_password'}
```

**Note:** The `user_registration_payload()` and `admin_registration_payload()` functions now automatically generate random passwords. You can pass a custom password if needed.

## Quick Start

### Configuration with Custom Domain

The SDK works with both local instances and custom domains in production:

**Local (development):**
```python
from keyrunes_sdk import KeyrunesClient

client = KeyrunesClient(base_url="http://localhost:3000")
```

**Production (custom domain):**
```python
from keyrunes_sdk import KeyrunesClient

# Use your Keyrunes domain
client = KeyrunesClient(
    base_url="https://auth.yourdomain.com",
    api_key="your-optional-api-key"  # If needed
)
```

**Environment variable:**
```python
import os
from keyrunes_sdk import KeyrunesClient

# Configure via environment variable
KEYRUNES_URL = os.getenv("KEYRUNES_BASE_URL", "http://localhost:3000")
client = KeyrunesClient(base_url=KEYRUNES_URL)
```

### Initializing the Client

```python
from keyrunes_sdk import KeyrunesClient

# Create client
client = KeyrunesClient(
    base_url="https://keyrunes.example.com",
    api_key="your-optional-api-key"
)

# Or use as context manager
with KeyrunesClient(base_url="https://keyrunes.example.com") as client:
    # Your code here
    pass
```

### Global Client (Recommended)

The most elegant way to use the library is to configure a global client once and use it throughout the project without passing the client in each decorator:

```python
from keyrunes_sdk import configure, require_group, require_admin

# Configure ONCE at application startup
client = configure("https://keyrunes.example.com")
client.login("admin@example.com", "password")

# Now use decorators WITHOUT passing the client!
@require_group("admins")
def delete_user(user_id: str):
    print(f"Deleting user {user_id}")

@require_admin()
def system_config(user_id: str):
    print(f"Configuring system")

# Use functions normally
delete_user(user_id="user123")  # No client needed!
system_config(user_id="admin123")  # No client needed!
```

**Example with multiple files:**

```python
# config.py
from keyrunes_sdk import configure

def init_app():
    client = configure("https://keyrunes.example.com")
    client.login("user@example.com", "password")

# services/admin.py
from keyrunes_sdk import require_group

@require_group("admins")  # No client needed!
def delete_user(user_id: str):
    pass

# main.py
from config import init_app
from services.admin import delete_user

init_app()  # Configure once
delete_user(user_id="123")  # Use anywhere!
```

> Tip: See `examples/global_client_usage.py` for a complete example!

### Authentication

#### Login

```python
# Login and get token
token = client.login("user@example.com", "password123")
print(f"Token: {token.access_token}")
print(f"User: {token.user.username}")

# Token is automatically configured in the client
```

#### User Registration

```python
# Register new user
user = client.register_user(
    username="newuser",
    email="newuser@example.com",
    password="securepass123",
    department="Engineering",  # Additional attributes
    role="Developer"
)

print(f"User created: {user.username}")
```

#### Admin Registration

```python
# Register admin (requires admin key)
admin = client.register_admin(
    username="adminuser",
    email="admin@example.com",
    password="securepass123",
    admin_key="secret-admin-key"
)

print(f"Admin created: {admin.username}")
```

### Group Verification

#### Manual Verification

```python
# Login first
client.login("user@example.com", "password")

# Check if user belongs to a group
has_access = client.has_group("user123", "admins")

if has_access:
    print("User has admin access!")
else:
    print("Access denied")
```

#### Get User Groups

```python
# Get current user groups
my_groups = client.get_user_groups()
print(f"My groups: {my_groups}")

# Get groups of another user
user_groups = client.get_user_groups("user123")
print(f"User groups: {user_groups}")
```

### Using Decorators

#### @require_group - Check Group

```python
from keyrunes_sdk import KeyrunesClient, require_group

client = KeyrunesClient("https://keyrunes.example.com")
client.login("admin@example.com", "password")

# Decorator: user needs to be in "admins" group
@require_group("admins", client=client)
def delete_user(user_id: str):
    print(f"Deleting user {user_id}")
    # Deletion code here

# Executes if user has the group, otherwise raises AuthorizationError
delete_user(user_id="user123")
```

#### Multiple Groups (ANY)

```python
# User needs to be in ANY of the groups
@require_group("admins", "moderators", all_groups=False)
def moderate_content(user_id: str, client: KeyrunesClient):
    print(f"Moderating content for {user_id}")

moderate_content(user_id="user123", client=client)
```

#### Multiple Groups (ALL)

```python
# User needs to be in ALL groups
@require_group("admins", "verified", all_groups=True)
def sensitive_operation(user_id: str, client: KeyrunesClient):
    print(f"Sensitive operation for {user_id}")

sensitive_operation(user_id="user123", client=client)
```

#### @require_admin - Check Admin

```python
from keyrunes_sdk import require_admin

# Only admins can execute
@require_admin(client=client)
def system_configuration(user_id: str):
    print(f"Configuring system for admin {user_id}")

system_configuration(user_id="admin123")
```

#### Decorator with Client in Kwargs

```python
# Pass client as function parameter
@require_group("admins")
def admin_function(user_id: str, client: KeyrunesClient):
    print(f"Admin function for {user_id}")

admin_function(user_id="user123", client=client)
```

## API Reference

### KeyrunesClient

#### Authentication Methods

- `login(username: str, password: str) -> Token`: Login
- `register_user(username: str, email: str, password: str, **attributes) -> User`: Register user
- `register_admin(username: str, email: str, password: str, admin_key: str, **attributes) -> User`: Register admin

#### User Methods

- `get_user(user_id: str) -> User`: Get user by ID
- `get_current_user() -> User`: Get current user (logged in)
- `get_user_groups(user_id: Optional[str] = None) -> List[str]`: Get user groups

## Complete API Reference

### KeyrunesClient Methods

#### Authentication

##### `login(username: str, password: str) -> Token`
Authenticates a user and returns an access token. The token is automatically configured in the client.

**Parameters:**
- `username`: Username or email of the user
- `password`: User password

**Returns:** `Token` object with `access_token`, `token_type`, `expires_in`, `refresh_token` (optional) and `user` (optional)

**Exceptions:**
- `AuthenticationError`: If credentials are invalid

**Example:**
```python
token = client.login("user@example.com", "password123")
print(f"Token: {token.access_token}")
print(f"User: {token.user.username if token.user else 'N/A'}")
```

#### Registration

##### `register_user(username: str, email: str, password: str, **attributes: Any) -> User`
Registers a new user in the system.

**Parameters:**
- `username`: Username (3-50 characters)
- `email`: User email (validated)
- `password`: Password (minimum 8 characters)
- `**attributes`: Additional attributes (e.g., `department="Engineering"`, `role="Developer"`)

**Returns:** Created `User` object

**Exceptions:**
- `AuthenticationError`: If registration fails
- `NetworkError`: If there is a network error or unexpected response format

**Example:**
```python
user = client.register_user(
    username="newuser",
    email="newuser@example.com",
    password="securepass123",
    department="Engineering",
    role="Developer"
)
```

##### `register_admin(username: str, email: str, password: str, admin_key: str, **attributes: Any) -> User`
Registers a new admin user in the system.

**Parameters:**
- `username`: Username (3-50 characters)
- `email`: Admin email (validated)
- `password`: Password (minimum 8 characters)
- `admin_key`: Admin registration key (must match server's `ADMIN_KEY`)
- `**attributes`: Additional attributes

**Returns:** Created `User` object with admin privileges

**Exceptions:**
- `AuthenticationError`: If registration fails
- `AuthorizationError`: If admin key is invalid
- `NetworkError`: If there is a network error or unexpected response format

**Example:**
```python
admin = client.register_admin(
    username="adminuser",
    email="admin@example.com",
    password="securepass123",
    admin_key="secret-admin-key"
)
```

#### User Query

##### `get_current_user() -> User`
Gets information about the currently authenticated user.

**Returns:** `User` object of the current user

**Exceptions:**
- `AuthenticationError`: If there is no valid token
- `NetworkError`: If there is a network error

**Example:**
```python
user = client.get_current_user()
print(f"User: {user.username}, Email: {user.email}")
print(f"Groups: {user.groups}")
```

##### `get_user(user_id: str) -> User`
Gets information about a specific user by ID.

**Parameters:**
- `user_id`: User ID

**Returns:** `User` object

**Exceptions:**
- `AuthenticationError`: If there is no valid token
- `UserNotFoundError`: If user does not exist
- `NetworkError`: If there is a network error

**Example:**
```python
user = client.get_user("user123")
```

#### Group Verification

##### `has_group(user_id: str, group_id: str) -> bool`
Checks if a user belongs to a specific group.

**Parameters:**
- `user_id`: User ID
- `group_id`: Group ID to verify

**Returns:** `True` if user belongs to the group, `False` otherwise

**Exceptions:**
- `AuthenticationError`: If there is no valid token
- `GroupNotFoundError`: If group does not exist or user is not in the group
- `NetworkError`: If there is a network error

**Example:**
```python
is_admin = client.has_group("user123", "admins")
if is_admin:
    print("User has admin privileges")
```

##### `get_user_groups(user_id: Optional[str] = None) -> List[str]`
Gets the list of groups for a user.

**Parameters:**
- `user_id` (optional): User ID. If `None`, returns groups of the current user

**Returns:** List of strings with group IDs

**Exceptions:**
- `AuthenticationError`: If there is no valid token
- `UserNotFoundError`: If user does not exist
- `NetworkError`: If there is a network error

**Example:**
```python
# Current user groups
my_groups = client.get_user_groups()

# Another user's groups
user_groups = client.get_user_groups("user123")
```

#### Utility Methods

##### `set_token(token: str) -> None`
Manually sets the authentication token in the client.

**Parameters:**
- `token`: JWT authentication token

**Example:**
```python
client.set_token("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
```

##### `clear_token() -> None`
Removes the authentication token from the client.

**Example:**
```python
client.clear_token()
```

##### `close() -> None`
Closes the HTTP session of the client. Useful for releasing resources.

**Example:**
```python
client.close()
```

##### Context Manager

The client can be used as a context manager to ensure automatic closing:

```python
with KeyrunesClient(base_url="https://keyrunes.example.com") as client:
    token = client.login("user@example.com", "password")
    user = client.get_current_user()
    # Client is automatically closed when exiting the block
```

### Decorators

#### @require_group

```python
@require_group(*group_ids, client=None, user_id_param="user_id", all_groups=False)
```

**Parameters:**
- `*group_ids`: Group IDs to check
- `client`: KeyrunesClient instance (optional if passed via kwargs)
- `user_id_param`: Name of the parameter containing user_id (default: "user_id")
- `all_groups`: If True, user needs ALL groups; if False, ANY group (default: False)

#### @require_admin

```python
@require_admin(client=None, user_id_param="user_id")
```

**Parameters:**
- `client`: KeyrunesClient instance (optional if passed via kwargs)
- `user_id_param`: Name of the parameter containing user_id (default: "user_id")

### Models (Pydantic)

Pydantic models are provided for convenience, but are optional. They are useful for:

- Data validation before sending to the API
- Parsing API responses
- Type hints and IDE autocomplete
- Data structure consistency

**Available models:**
- `User`: User model
- `Group`: Group model
- `Token`: Authentication token model
- `UserRegistration`: User registration data
- `AdminRegistration`: Admin registration data
- `LoginCredentials`: Login credentials
- `GroupCheck`: Group verification result

#### Using with Flask, FastAPI or Django

If you are using Flask, FastAPI or Django, you can:

**Option 1: Use SDK models and map to your models**

```python
from keyrunes_sdk import KeyrunesClient
from keyrunes_sdk.models import User
from your_app.models import MyUser  # Your SQLAlchemy/Django ORM model

client = KeyrunesClient("https://keyrunes.example.com")
token = client.login("user@example.com", "password")

# Get data from Keyrunes
keyrunes_user = client.get_current_user()  # Returns SDK User

# Map to your model
my_user = MyUser(
    id=keyrunes_user.id,
    username=keyrunes_user.username,
    email=keyrunes_user.email,
    groups=keyrunes_user.groups,
    # Add your own fields
    created_at=datetime.now(),
    # ... other fields from your model
)
```

**Option 2: Work with dictionaries**

```python
from keyrunes_sdk import KeyrunesClient

client = KeyrunesClient("https://keyrunes.example.com")
response = client._make_request("GET", "/api/v1/users/me")
# response is a dict, use as needed
user_data = response  # {'id': '...', 'username': '...', ...}
```

**Option 3: Use only SDK models**

SDK models are Pydantic, so they work well with FastAPI directly:

```python
from fastapi import FastAPI
from keyrunes_sdk import KeyrunesClient
from keyrunes_sdk.models import User

app = FastAPI()
client = KeyrunesClient("https://keyrunes.example.com")

@app.get("/me", response_model=User)
async def get_current_user():
    return client.get_current_user()
```

**Note:** SDK models are mainly for validation and parsing. You can add your own fields in your project models (Flask-SQLAlchemy, Django ORM, etc.) and map Keyrunes data as needed.

### Exceptions

- `KeyrunesError`: Base exception
- `AuthenticationError`: Authentication error
- `AuthorizationError`: Authorization error
- `GroupNotFoundError`: Group not found
- `UserNotFoundError`: User not found
- `NetworkError`: Network error

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/Keyrunes/keyrunes-python-sdk.git
cd keyrunes-python-sdk

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

### Run Tests

```bash
# Run all tests
poetry run pytest

# With verbose
poetry run pytest -v

# With coverage
poetry run pytest --cov=keyrunes_sdk --cov-report=html

# Run specific tests
poetry run pytest tests/test_client.py
poetry run pytest tests/test_decorators.py
poetry run pytest tests/test_models.py
```

### Local Testing with Docker Compose

Test the library against a real Keyrunes instance running locally:

#### 1. Start Keyrunes

```bash
# Start all services (Keyrunes, PostgreSQL, Redis)
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f keyrunes
```

**Available services:**
- Keyrunes API: http://localhost:3000
- PostgreSQL: localhost:5432

#### 2. Run Integration Tests

```bash
# Complete test script
poetry run python examples/test_local.py

# Or using taskipy
poetry run task test-local
```

#### 3. Run Examples

```bash
# Basic usage example
poetry run python examples/basic_usage.py

# Or using taskipy
poetry run task example-basic
```

#### 4. Stop Services

```bash
# Stop containers
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Linting and Formatting

```bash
# Black (formatting)
poetry run black keyrunes_sdk tests

# isort (organize imports)
poetry run isort keyrunes_sdk tests

# flake8 (linting)
poetry run flake8 keyrunes_sdk tests

# mypy (type checking)
poetry run mypy keyrunes_sdk
```

## Tests

The library has 86% test coverage using:

- pytest: Test framework
- factory-boy: Factories for creating test data
- faker: Fake data generation for tests
- pytest-cov: Code coverage
- pytest-mock: Mocking

### Test Structure

```
tests/
├── __init__.py
├── conftest.py          # Fixtures and configurations
├── factories.py         # Factory Boy factories
├── test_client.py       # Client tests
├── test_decorators.py   # Decorator tests
└── test_models.py       # Model tests
```

## Security

- All passwords must have at least 8 characters
- JWT tokens are used for authentication
- HTTPS is recommended for production
- Email validation using email-validator

## License

MIT License - see [LICENSE](LICENSE) for more details.

## Contributing

Contributions are welcome! Please:

1. Fork the project
2. Create a branch for your feature (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Support

- [Report Bug](https://github.com/Keyrunes/keyrunes/issues)
- [Discussions](https://github.com/Keyrunes/keyrunes/discussions)
- Email: keyrunes@example.com

## Links

- [Keyrunes Main Repository](https://github.com/Keyrunes/keyrunes)
- [Complete Documentation](https://keyrunes.example.com/docs)
- [PyPI Package](https://pypi.org/project/keyrunes-sdk/)

---

Made with love for the Keyrunes community
