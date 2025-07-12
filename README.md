# Definite SDK

A Python client for interacting with the Definite API, providing a convenient interface for key-value store operations, SQL query execution, and data integration management.

## Installation

**pip:**
```bash
pip install definite-sdk
```

**poetry:**
```bash
poetry add definite-sdk
```

## Quick Start

```python
from definite_sdk import DefiniteClient

# Initialize the client
client = DefiniteClient("YOUR_API_KEY")
```

## Features

### 🗄️ Key-Value Store

Store and retrieve key-value pairs that can be accessed by custom Python scripts hosted on Definite.

```python
# Initialize or retrieve an existing key-value store
store = client.get_kv_store('test_store')

# Add or update key-value pairs
store['replication_key'] = 'created_at'
store['replication_state'] = '2024-05-20'

# Commit changes
store.commit()

# Retrieve values
print(store['replication_key'])  # 'created_at'
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

# List all integrations
integrations = list(integration_store.list_integrations())

# Get a specific integration
integration = integration_store.get_integration("my_integration")
```

## Authentication

To use the Definite SDK, you'll need an API key. You can find and copy your API key from the bottom left user menu in your Definite workspace.

For SQL queries, you'll also need your integration ID, which can be found in your integration's page URL.

## Error Handling

The SDK uses standard HTTP status codes and raises `requests.HTTPError` for API errors:

```python
import requests

try:
    result = sql_client.execute("SELECT * FROM invalid_table")
except requests.HTTPError as e:
    print(f"API Error: {e}")
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.

## Documentation

For more detailed documentation, visit: https://docs.definite.app/

## Support

If you encounter any issues or have questions, please reach out to hello@definite.app
