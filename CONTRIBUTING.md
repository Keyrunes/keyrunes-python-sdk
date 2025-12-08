# Contributing to Keyrunes Python SDK

First off, thank you for considering contributing to Keyrunes Python SDK! Whether it's code, documentation, bug reports, or feature requests, your help makes Keyrunes SDK better for everyone. This guide will help you get started and make the process smooth for you and the maintainers.

---

## Table of Contents

1. [How to Contribute](#how-to-contribute)
2. [Reporting Bugs](#reporting-bugs)
3. [Requesting Features](#requesting-features)
4. [Development Setup](#development-setup)
5. [Code Style and Standards](#code-style-and-standards)
6. [Submitting Pull Requests](#submitting-pull-requests)
7. [Community Guidelines](#community-guidelines)
8. [Acknowledgements](#acknowledgements)

---

## How to Contribute

There are many ways you can contribute:

- **Code Contributions**: Fix bugs, implement new features, or improve existing code.
- **Documentation**: Improve README, write guides, or clarify examples.
- **Testing**: Add or improve unit, integration, or end-to-end tests.
- **Feedback**: Report issues, suggest features, or provide performance insights.

Before contributing code, please check the existing issues to avoid duplication.

---

## Reporting Bugs

If you find a bug, please submit an issue with:

- A clear and descriptive title.
- Steps to reproduce the problem.
- Expected vs actual behavior.
- Relevant environment information (OS, Python version, etc.).
- Logs or screenshots, if applicable.

This helps maintainers reproduce and fix the issue faster.

---

## Requesting Features

Feature requests should include:

- A clear description of the feature.
- Why it is needed and how it improves Keyrunes SDK.
- Optional examples or mockups.

Feature requests are discussed openly and may be implemented collaboratively.

---

## Development Setup

Follow these steps to get Keyrunes SDK running locally:

1. **Clone the repository:**
```bash
   git clone https://github.com/jonatasoli/keyrunes-python-sdk.git
   cd keyrunes-python-sdk
```

2. **Install Poetry** (if not already installed):
```bash
   curl -sSL https://install.python-poetry.org | python3 -
```

3. **Install dependencies:**
```bash
   poetry install
```

4. **Start Keyrunes server** (using Docker Compose):
```bash
   docker-compose up -d
```

   Wait a few seconds for the services to start, then verify:
```bash
   curl http://localhost:8080/health
```

5. **Run tests:**
```bash
   poetry run pytest
```

   Or with coverage:
```bash
   poetry run pytest --cov=keyrunes_sdk --cov-report=html
```

6. **Run example scripts:**
```bash
   poetry run python examples/test_local.py
   poetry run python examples/basic_usage.py
   poetry run python examples/global_client_usage.py
```

---

## Code Style and Standards

Follow Python community conventions and PEP 8 style guide.

### Formatting

- Use **Black** for code formatting (line length: 100)
- Use **isort** for import sorting
- Run formatting before committing:
```bash
   poetry run black keyrunes_sdk tests examples
   poetry run isort keyrunes_sdk tests examples
```

### Type Hints

- Use type hints for all function parameters and return types
- Run type checking with mypy:
```bash
   poetry run mypy keyrunes_sdk
```

### Linting

- Use **flake8** for linting:
```bash
   poetry run flake8 keyrunes_sdk tests
```

### Testing

- Write tests for all new features and bug fixes
- Maintain test coverage above 95%
- Use descriptive test names
- Follow the existing test structure

### Documentation

- Write docstrings for all public functions and classes
- Use Google-style docstrings
- Keep comments in English
- Do not use emojis in comments
- Do not use hyphens in comments

### Code Quality

- Use meaningful variable and function names
- Keep code modular and well-documented
- Write tests for new features and bug fixes
- Ensure all tests pass before submitting

### Pre-commit Checklist

Before submitting a pull request, ensure:

- [ ] All tests pass: `poetry run pytest`
- [ ] Code is formatted: `poetry run black --check .`
- [ ] Imports are sorted: `poetry run isort --check-only .`
- [ ] No linting errors: `poetry run flake8 .`
- [ ] Type checking passes: `poetry run mypy keyrunes_sdk`
- [ ] Test coverage is maintained: `poetry run pytest --cov=keyrunes_sdk`
- [ ] Documentation is updated if needed

---

## Submitting Pull Requests

1. **Fork the repository.**

2. **Create a new branch** for your feature/bugfix:
```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bugfix-name
```

3. **Write code and tests** according to the guidelines.

4. **Ensure all tests pass:**
```bash
   poetry run pytest
```

5. **Format and lint your code:**
```bash
   poetry run task format
   poetry run task lint
   poetry run task type-check
```

6. **Commit your changes** with clear, descriptive commit messages:
```bash
   git commit -m "Add feature: description of what you added"
   git commit -m "Fix bug: description of what you fixed"
```

7. **Push to your fork:**
```bash
   git push origin feature/your-feature-name
```

8. **Submit a pull request** with:
   - A clear title and description
   - Reference to related issues (if any)
   - Description of changes made
   - Any breaking changes (if applicable)

Pull requests are reviewed collaboratively. Be prepared to make changes based on feedback.

---

## Community Guidelines

We value respectful and constructive communication. Please follow:

- Be respectful to all contributors.
- Provide clear and concise feedback.
- Stay on-topic and avoid off-topic discussions in issues/PRs.
- Follow the [Code of Conduct](CODE_OF_CONDUCT.md).

---

## Acknowledgements

Thank you to all contributors who have helped make Keyrunes Python SDK better!

For questions or support, please open an issue or contact the maintainers.

---

## Additional Resources

- [Keyrunes Main Repository](https://github.com/Keyrunes/keyrunes)
- [Python SDK Documentation](README.md)
- Testing Guide: Veja a seção de testes no README.md
- [Publishing Guide](PUBLISHING.md)

