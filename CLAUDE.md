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

1. **DefiniteClient** (client.py): Main entry point that creates the per-feature clients below
2. **Clients**:
   - **DefiniteKVStore** (store.py): Dictionary-like persistent key-value storage with version control
   - **DefiniteSecretStore** (secret.py): Direct API for managing application secrets
   - **DefiniteIntegrationStore** (integration.py): Read-only access to integration configurations (credentials live in each integration's `details` dict)
   - **DefiniteSqlClient** (sql.py): Execute SQL (against integrations or the `LAKE.<schema>.<table>` data lake) and Cube queries
   - **DefiniteDriveClient** (drive.py): Write files to Definite Drive; pair with the SQL client to load data into the lake
   - **DefiniteMessageClient** (message.py): Send messages via channels (e.g. Slack)
   - **DefiniteDLTPipeline** (dlt.py): dlt pipeline wrapper that persists state to a KV store

Key architectural decisions:
- KV Store uses optimistic locking with version IDs to prevent conflicts
- KV Store requires explicit `commit()` to persist changes (transactional model); keys/values must be strings
- Secret, Integration, Drive, and SQL operations persist/execute immediately
- Writing to the data lake: the supported path is Drive + SQL (`get_drive_client().write_temporary_file(...)` then `get_sql_client().execute("CREATE/INSERT/MERGE ... read_parquet('{gcs_path}')")`). `attach_ducklake()` is deprecated and unsupported for workload-identity-only teams.
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
