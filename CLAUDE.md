# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
poetry install

# Run tests (requires DEF_API_KEY environment variable)
DEF_API_KEY=your_api_key poetry run pytest

# Run specific test
DEF_API_KEY=your_api_key poetry run pytest tests/test_store.py::test_kv_store_operations

# Code formatting
poetry run black .

# Linting
poetry run flake8

# Type checking
poetry run mypy definite_sdk/
```

## Architecture Overview

This SDK provides Python clients for Definite's cloud storage API (https://api.definite.app). The codebase follows a simple client-factory pattern:

1. **DefiniteClient** (client.py): Main entry point that creates store instances
2. **Store Implementations**:
   - **DefiniteKVStore** (store.py): Dictionary-like persistent key-value storage with version control
   - **DefiniteSecretStore** (secret.py): Direct API for managing application secrets
   - **DefiniteIntegrationStore** (integration.py): Read-only access to integration configurations

Key architectural decisions:
- KV Store uses optimistic locking with version IDs to prevent conflicts
- KV Store requires explicit `commit()` to persist changes (transactional model)
- Secret and Integration stores persist changes immediately
- All API calls use Bearer token authentication
- No caching - each operation makes direct API calls

## Known Issues

- integration.py incorrectly uses `SECRET_STORE_ENDPOINT` instead of a proper integration endpoint constant