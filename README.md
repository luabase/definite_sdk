# Definite SDK

A Python client for interacting with the Definite API, providing a convenient interface for key-value store operations, SQL query execution, secrets management, and DLT (Data Load Tool) integration with state persistence.

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
- **dlt Integration**: Run dlt pipelines with automatic state persistence to Definite
- **DuckDB Support**: Automatic discovery and connection to team's DuckDB integrations

## Basic Usage

### 🗄️ Key-Value Store

Store and retrieve key-value pairs that can be accessed by custom Python scripts hosted on Definite.

```python
# Initialize or retrieve an existing key-value store
store = client.get_kv_store('test_store')
# Or use the alias method
store = client.kv_store('test_store')

# Add or update key-value pairs
store['replication_key'] = 'created_at'
store['replication_state'] = '2024-05-20'
store["key1"] = "value1"
store["key2"] = {"nested": "data"}

# Commit changes
store.commit()

# Retrieve values
print(store['replication_key'])  # 'created_at'
value = store["key1"]
```

### 🗃️ SQL Query Execution

Execute SQL queries against your connected database integrations.

```python
# Initialize the SQL client
sql_client = client.get_sql_client()

# Execute a SQL query
result = sql_client.execute("SELECT * FROM users LIMIT 10")
print(result)

# Execute a SQL query with a specific integration
result = sql_client.execute(
    "SELECT COUNT(*) FROM orders WHERE status = 'completed'",
    integration_id="my_database_integration"
)
print(result)
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

Manage your data integrations and connections.

```python
# Initialize the integration store
integration_store = client.get_integration_store()
# Or use the alias method
integration_store = client.integration_store()

# List all integrations
integrations = list(integration_store.list_integrations())

# Get a specific integration
integration = integration_store.get_integration("my_integration")
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
