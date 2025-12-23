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

## Publishing to PyPI

To publish a new version:

1. **Bump the version** in `pyproject.toml`:
   ```toml
   version = "0.1.X"  # increment the patch version
   ```

2. **Create a PR** with the version bump and merge to `main`

3. **Trigger the publish workflow** via GitHub CLI:
   ```bash
   gh workflow run publish.yml
   ```

   Or manually via GitHub Actions: https://github.com/luabase/definite_sdk/actions/workflows/publish.yml

4. **Monitor the workflow** to ensure it completes successfully:
   ```bash
   gh run list --workflow=publish.yml --limit=1
   gh run watch <run_id>
   ```

The workflow will:
- Build the package
- Create a GitHub release with tag `v{version}`
- Publish to PyPI

**Important**: The version in `pyproject.toml` must be incremented before running the publish workflow, otherwise the "Create GitHub Release" step will fail with "Release.tag_name already exists".

## Known Issues

- integration.py incorrectly uses `SECRET_STORE_ENDPOINT` instead of a proper integration endpoint constant