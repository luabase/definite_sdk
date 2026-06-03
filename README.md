# Definite SDK

A Python client for interacting with the Definite API, providing a convenient interface for key-value store operations, SQL query execution, secrets management, messaging capabilities, and DLT (Data Load Tool) integration with state persistence.

## Installation

**pip:**
```bash
pip install definite-sdk

# For dlt support
pip install "definite-sdk[dlt]"
```

**poetry:**
```bash
poetry add definite-sdk

# For dlt support
poetry add "definite-sdk[dlt]"
```

## Quick Start

```python
from definite_sdk import DefiniteClient

# Initialize the client
client = DefiniteClient("YOUR_API_KEY")
```

## Features

- **Key-Value Store**: Persistent storage with version control and transactional commits
- **SQL Query Execution**: Execute SQL queries against your connected database integrations
- **Cube Query Execution**: Execute Cube queries for advanced analytics and data modeling
- **Secret Management**: Secure storage and retrieval of application secrets
- **Integration Store**: Read-only access to integration configurations
- **Messaging**: Send messages through various channels (Slack, and more coming soon)
- **dlt Integration**: Run dlt pipelines with automatic state persistence to Definite
- **DuckLake Integration**: Easy attachment of your team's DuckLake to DuckDB connections
- **DuckDB Support**: Automatic discovery and connection to team's DuckDB integrations

## Which method for which task

| Task | Entry point | Key methods | Persistence |
|------|-------------|-------------|-------------|
| Read integration credentials/config | `client.get_integration_store()` | `get_integration(name)`, `get_integration_by_id(id)`, `list_integrations()` | read-only |
| Store/retrieve your own secrets | `client.get_secret_store()` | `set_secret`, `get_secret`, `list_secrets`, `delete_secret` | immediate |
| Read from the data lake / databases | `client.get_sql_client()` | `execute(sql)`, `execute_cube_query(...)` | n/a |
| Write to the data lake (recommended) | `client.get_drive_client()` + `client.get_sql_client()` | `write_temporary_file(...)` then `execute("CREATE/INSERT/MERGE ...")` | immediate |
| Write to the data lake (legacy) | `client.attach_ducklake()` | returns SQL to attach DuckLake to a local DuckDB — **deprecated** | immediate |
| Persist key-value state | `client.get_kv_store(name)` | `store[key] = value`, then `store.commit()` | **explicit `commit()`** |
| Send messages (Slack, …) | `client.get_message_client()` | `send_message(...)`, `send_slack_message(...)` | immediate |

The data lake is a **DuckLake** warehouse addressed in SQL as `LAKE.<schema>.<table>`.

## Basic Usage

### 🗄️ Key-Value Store

Store and retrieve key-value pairs that can be accessed by custom Python scripts hosted on Definite.

The store behaves like a Python dict in memory, but **nothing is saved until you call `commit()`**. Keys and values must both be strings — JSON-encode anything more complex.

```python
import json

# Initialize or retrieve an existing key-value store
store = client.get_kv_store('test_store')
# Or use the alias method
store = client.kv_store('test_store')

# Add or update key-value pairs (values must be strings)
store['replication_key'] = 'created_at'
store['replication_state'] = '2024-05-20'
store["key1"] = "value1"
store["key2"] = json.dumps({"nested": "data"})  # JSON-encode non-string values

# Commit changes (REQUIRED — without this, nothing is persisted)
store.commit()

# Retrieve values
print(store['replication_key'])         # 'created_at'
value = store["key1"]                    # "value1"
nested = json.loads(store["key2"])       # {"nested": "data"}
missing = store.get("absent", "default") # dict-style get with default
```

**Versioning / conflict handling:** the store loads a `version_id` when you open it and sends it on `commit()`. If someone else committed in the meantime, your `commit()` raises rather than silently overwriting their changes (optimistic locking). Re-open the store and re-apply your changes to retry. Call `store.delete()` to permanently remove the whole store.

### 🗃️ SQL Query Execution

Execute SQL queries against your connected database integrations, or against the data lake (`LAKE.<schema>.<table>`).

```python
# Initialize the SQL client
sql_client = client.get_sql_client()

# Read from a data lake table
result = sql_client.execute("SELECT * FROM LAKE.MY_SCHEMA.events LIMIT 10")

# Execute a SQL query against a specific integration
# (integration_id is the ID from the integration's page URL; omit it to use the default)
result = sql_client.execute(
    "SELECT COUNT(*) FROM orders WHERE status = 'completed'",
    integration_id="my_database_integration"
)
```

`execute()` returns a parsed JSON dict shaped like:

```python
{
    "success": True,
    "columns": ["id", "name"],
    "data": [
        {"id": 1, "name": "John"},
        {"id": 2, "name": "Jane"},
    ],
}

# Access rows:
for row in result["data"]:
    print(row["name"])
```

### 📊 Cube Query Execution

Execute Cube queries for advanced analytics and data modeling.

```python
# Prepare a Cube query
cube_query = {
    "dimensions": [],
    "measures": ["sales.total_amount"],
    "timeDimensions": [{
        "dimension": "sales.date", 
        "granularity": "month"
    }],
    "limit": 1000
}

# Execute the Cube query
result = sql_client.execute_cube_query(
    cube_query, 
    integration_id="my_cube_integration"
)
print(result)
```

### 🏞️ Writing to the Data Lake

The recommended way to load data into the lake is **Drive + SQL**: upload a file (parquet/csv) to Definite Drive, then run a SQL statement that reads it into a `LAKE.<schema>.<table>` table. This works for all teams (including workload-identity-only teams provisioned after April 2026).

```python
import io
import pandas as pd

drive = client.get_drive_client()   # alias: client.drive_client()
sql_client = client.get_sql_client()

# 1. Turn a DataFrame into parquet bytes
df = pd.DataFrame([{"id": 1, "name": "alice"}, {"id": 2, "name": "bob"}])
buf = io.BytesIO()
df.to_parquet(buf)

# 2. Upload to a temporary, auto-expiring location in Drive
result = drive.write_temporary_file(buf.getvalue(), name="users.parquet", ttl_days=7)
# result.gcs_path -> "gs://.../users.parquet", usable directly in SQL

# 3a. CREATE (or replace) a lake table from the uploaded file
sql_client.execute(
    f"CREATE OR REPLACE TABLE LAKE.MY_SCHEMA.users AS "
    f"SELECT * FROM read_parquet('{result.gcs_path}')"
)

# 3b. INSERT (append) into an existing table
sql_client.execute(
    f"INSERT INTO LAKE.MY_SCHEMA.users "
    f"SELECT * FROM read_parquet('{result.gcs_path}')"
)

# 3c. MERGE / upsert on a key
sql_client.execute(f"""
    MERGE INTO LAKE.MY_SCHEMA.users AS t
    USING (SELECT * FROM read_parquet('{result.gcs_path}')) AS s
    ON t.id = s.id
    WHEN MATCHED THEN UPDATE SET *
    WHEN NOT MATCHED THEN INSERT *
""")
```

**Drive write methods** (`client.get_drive_client()`):

- `write_temporary_file(data, name=..., ttl_days=1..30)` — server picks a path under `_tmp/<date>/<uuid>/<name>`, auto-deleted after the TTL. Use it to stage data for a one-time ingest.
- `write_file(data, path="folder/file.parquet")` — persistent file at an explicit path, kept until you delete it.

Both accept `bytes`, `str`, a filesystem path, or a binary file-like object, and return a `DriveWriteResult` with:

- `gcs_path` — full `gs://` URI; use this in SQL (`read_parquet(...)`, `read_csv(...)`, …).
- `drive_path` — the path a pipeline sandbox sees (`/home/user/drive/...`).
- `path` — the drive-relative path (e.g. `ingest/events.parquet`).
- `expires_at` — ISO 8601 deletion time (temporary writes only).

### 🔒 Secret Store

Securely store and retrieve secrets for your integrations.

```python
# Initialize the secret store
secret_store = client.get_secret_store()
# Or use the alias method
secret_store = client.secret_store()

# Set a secret
secret_store.set_secret("database_password", "my_secure_password")

# Get a secret
password = secret_store.get_secret("database_password")

# List all secrets
secrets = list(secret_store.list_secrets())
```

### 🔗 Integration Management

Read-only access to your integrations. Credentials and config live in the integration's `details` dict — this is how you obtain an integration's API key, host, tokens, etc.

```python
# Initialize the integration store
integration_store = client.get_integration_store()
# Or use the alias method
integration_store = client.integration_store()

# List all integrations (optionally filter by type or category)
integrations = integration_store.list_integrations()                       # all
integrations = integration_store.list_integrations(integration_type="slack")
# Each item in list_integrations() is {"id": <id>, **details} — id + flattened details.

# Get a specific integration's details (by name or by id)
details = integration_store.get_integration("my_integration")        # returns the details dict
details = integration_store.get_integration_by_id("integration_uuid")

# Read a credential / config value out of the details dict
api_key = details.get("api_key")
host = details.get("host")
```

> Note the return-shape difference: `list_integrations()` injects the `id` and flattens the
> details into each record, while `get_integration()` / `get_integration_by_id()` return only
> the `details` dict (no `id`). Both raise if nothing matches.

You can also inspect an integration's sync (DAG) runs:

```python
runs = integration_store.get_syncs("integration_id", limit=50, status="FAILED")
latest = integration_store.get_latest_sync("integration_id")
```

### 💬 Messaging

Send messages through various channels using the messaging client.

```python
# Initialize the message client
message_client = client.get_message_client()
# Or use the alias method
message_client = client.message_client()

# Send a Slack message using the unified interface
result = message_client.send_message(
    channel="slack",
    integration_id="your_slack_integration_id",
    to="C0920MVPWFN",  # Slack channel ID
    content="Hello from Definite SDK! 👋"
)

# Send a Slack message with blocks and threading
result = message_client.send_message(
    channel="slack",
    integration_id="your_slack_integration_id",
    to="C0920MVPWFN",
    content="Fallback text",
    blocks=[{
        "type": "section",
        "text": {"type": "mrkdwn", "text": "*Important Update*"}
    }],
    thread_ts="1234567890.123456"  # Reply in thread
)

# Or use the convenience method for Slack
result = message_client.send_slack_message(
    integration_id="your_slack_integration_id",
    channel_id="C0920MVPWFN",
    text="Quick message using the convenience method!",
    blocks=[{
        "type": "section",
        "text": {"type": "mrkdwn", "text": "Message with *rich* _formatting_"}
    }]
)
```

### dlt Integration

```python
from definite_sdk.dlt import DefiniteDLTPipeline
import dlt

# Create an incremental resource
@dlt.resource(primary_key="id", write_disposition="merge")
def orders(cursor=dlt.sources.incremental("created_at")):
    # Your data loading logic here
    pass

# Create and run pipeline
pipeline = DefiniteDLTPipeline("orders_sync")
pipeline.run(orders())

# State is automatically persisted to Definite
last_cursor = pipeline.get_state("orders")
```

### DuckLake Integration (legacy / deprecated)

> ⚠️ **Deprecated.** `attach_ducklake()` only works for legacy teams that have HMAC keys or a
> service-account JSON on their DuckLake integration. Teams provisioned after **April 2026** use
> workload-identity-only auth and will raise `UnsupportedDuckLakeAttachError`, since those
> credentials cannot be replicated on a customer laptop. Calling it also emits a
> `DeprecationWarning`. **Use the [Writing to the Data Lake](#-writing-to-the-data-lake)
> (Drive + SQL) workflow instead** — it works for all teams.

Attach your team's DuckLake to a local DuckDB connection for direct data access:

```python
import duckdb
from definite_sdk import DefiniteClient

# Initialize the client
client = DefiniteClient("YOUR_API_KEY")

# Connect to DuckDB and attach DuckLake (raises UnsupportedDuckLakeAttachError on newer teams)
conn = duckdb.connect()
conn.execute(client.attach_ducklake())

# Now you can use DuckLake tables
conn.execute("CREATE SCHEMA IF NOT EXISTS lake.my_schema;")
conn.execute("CREATE OR REPLACE TABLE lake.my_schema.users AS SELECT * FROM df")

# Query your DuckLake data
result = conn.sql("SELECT * FROM lake.my_schema.users").df()
```

You can also specify a custom alias for the attached DuckLake:

```python
# Attach with custom alias
conn.execute(client.attach_ducklake(alias="warehouse"))

# Use the custom alias
conn.execute("SELECT * FROM warehouse.my_schema.users")
```

### DuckDB Integration Discovery

```python
from definite_sdk.dlt import get_duckdb_connection

# Automatically discovers DuckDB integration using DEFINITE_API_KEY env var
result = get_duckdb_connection()
if result:
    integration_id, connection = result
    # Use the DuckDB connection
    connection.execute("SELECT * FROM my_table")
```

**Note**: DuckDB integration discovery is currently limited as the API only exposes source integrations, not destination integrations. This functionality is provided for future compatibility.

### State Management

```python
# Set custom state
pipeline.set_state("custom_key", "custom_value")

# Get all state
all_state = pipeline.get_state()

# Resume from previous state
pipeline.resume_from_state()

# Reset state
pipeline.reset_state()
```

## Authentication

To use the Definite SDK, you'll need an API key. You can find and copy your API key from the bottom left user menu in your Definite workspace.

For SQL queries, you'll also need your integration ID, which can be found in your integration's page URL.

## Environment Variables

- `DEFINITE_API_KEY`: Your Definite API key (auto-injected in Definite runtime)
- `DEF_API_KEY`: Alternative environment variable for API key

## Error Handling

The SDK uses standard HTTP status codes and raises `requests.HTTPError` for API errors:

```python
import requests

try:
    result = sql_client.execute("SELECT * FROM invalid_table")
except requests.HTTPError as e:
    print(f"API Error: {e}")
```

## Testing

```bash
# Run all tests
DEF_API_KEY=your_api_key poetry run pytest

# Run specific test file
DEF_API_KEY=your_api_key poetry run pytest tests/test_dlt.py
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.

## Documentation

For more detailed documentation, visit: https://docs.definite.app/

## Support

If you encounter any issues or have questions, please reach out to hello@definite.app
