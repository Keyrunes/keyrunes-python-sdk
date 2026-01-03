# Keyrunes SDK Examples

This directory contains example scripts demonstrating how to use the Keyrunes Python SDK.

## Prerequisites

Before running the examples, make sure you have:

1. **Keyrunes server running** (via Docker Compose):
```bash
   docker-compose up -d
```

2. **Wait for services to start**:
```bash
   # Check from inside container (this should work)
   docker-compose exec keyrunes curl http://127.0.0.1:3000/api/health

   # Or try from host (port 3000)
   curl http://localhost:3000/api/health
```


3. **Install dependencies**:
```bash
   poetry install
```

## Available Examples

### 1. `test_local.py`

This script runs a comprehensive test suite against a local Keyrunes instance, testing all SDK functionality.

**What it tests:**
- User registration
- User login
- Admin registration
- Getting current user
- Group verification
- Decorators (`@require_group`, `@require_admin`)
- Context manager usage

**How to run:**
```bash
   poetry run python examples/test_local.py
```

**Expected output:**
- Test results for each functionality
- Success/error messages for each test
- Summary at the end

---

### 2. `basic_usage.py` - Basic Usage Example

This example demonstrates the fundamental features of the SDK in a simple, step-by-step manner.

**What it demonstrates:**
- Creating a client
- Registering a new user
- Logging in
- Getting user information
- Checking group membership
- Using decorators
- Registering an admin
- Using context manager

**How to run:**
```bash
   poetry run python examples/basic_usage.py
```

**Note:** This example will create test users. Make sure Keyrunes is running and accessible.

---

### 3. `global_client_usage.py` - Global Client Pattern

This example shows the recommended way to use the SDK in larger applications, using a global client configuration.

**What it demonstrates:**
- Configuring a global client once
- Using decorators without passing client explicitly
- Multiple decorator patterns (single group, multiple groups, admin-only)
- Organizing code across multiple files

**How to run:**
```bash
   poetry run python examples/global_client_usage.py
```

**Key concepts:**
- Configure once at application startup
- Use decorators anywhere without passing client
- Cleaner, more maintainable code structure

---

## Troubleshooting

### Keyrunes is not available

If you see errors about Keyrunes not being available:

1. **Check if Docker Compose is running:**
```bash
   docker-compose ps
```

2. **Check Keyrunes health (try both endpoints):**
```bash
   # Try the API health endpoint
   curl http://localhost:3000/api/health

   # Or check from inside the container
   docker-compose exec keyrunes curl http://127.0.0.1:3000/api/health
```

3. **View logs:**
```bash
   docker-compose logs keyrunes
```

4. **Restart services:**
```bash
   docker-compose restart keyrunes
```

5. **If connection is reset, try recreating the container:**
```bash
   docker-compose down keyrunes
   docker-compose up -d keyrunes
   sleep 10  # Wait for service to start
   curl http://localhost:3000/api/health
```

**Note:** If you see "Connection reset by peer", the service may be binding to `127.0.0.1`. Check the logs; with `network_mode: host` or `ROCKET_ADDRESS=0.0.0.0` it exposes on port `3000`.

### Port already in use

If port 3000 is already in use:

1. **Find what's using the port:**
```bash
   lsof -i :3000  # macOS/Linux
   netstat -ano | findstr :3000  # Windows
```

2. **Change port in docker-compose.yml** or stop the conflicting service

### Test user already exists

If you get errors about users already existing:

1. **Stop and clean Docker volumes:**
```bash
   docker-compose down -v
   docker-compose up -d
```

2. **Or use different usernames/emails** in the example scripts

---

## Integration with Flask, FastAPI, or Django

The SDK models (`User`, `Token`, etc.) are provided for convenience but are **optional**. You can:

### Option 1: Use SDK Models (Recommended for Quick Start)

```python
from keyrunes_sdk import KeyrunesClient
from keyrunes_sdk.models import User, Token

client = KeyrunesClient("https://keyrunes.example.com")
token = client.login("user@example.com", "password")
user = client.get_current_user()  # Returns SDK User model
```

### Option 2: Use Your Own Models (Recommended for Production)

You can use the SDK client methods and map responses to your own models:

```python
from keyrunes_sdk import KeyrunesClient
from your_app.models import MyUser  # Your Flask/SQLAlchemy/Django model

client = KeyrunesClient("https://keyrunes.example.com")
token = client.login("user@example.com", "password")

# Get user data from Keyrunes
user_data = client.get_current_user()

# Map to your own model
my_user = MyUser(
    id=user_data.id,
    username=user_data.username,
    email=user_data.email,
    groups=user_data.groups,
    # Add your own fields
)
```

### Option 3: Use Raw Responses

You can also work with raw dictionaries:

```python
from keyrunes_sdk import KeyrunesClient

client = KeyrunesClient("https://keyrunes.example.com")
response = client._make_request("GET", "/api/users/me")
# response is a dict, use it as needed
```

**Note:** The SDK models are useful for:
- Type hints and IDE autocomplete
- Data validation before sending to API
- Consistent response parsing
- But they're not required if you prefer your own models

---

## Next Steps

After running the examples:

1. **Read the main README** for detailed API documentation
2. **Check CONTRIBUTING.md** if you want to contribute
3. **Explore the source code** in `keyrunes_sdk/` directory

---

## Need Help?

- Open an issue on GitHub
- Check the main README.md
- Review the test files in `tests/` directory
- See the source code documentation
