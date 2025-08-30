#!/usr/bin/env python3
"""
Example script demonstrating the usage of Definite SDK SQL functionality.

This script shows how to:
1. Initialize the Definite client
2. Execute SQL queries against database integrations
3. Execute Cube queries for analytics
4. Handle errors appropriately
"""

import os
import sys
from definite_sdk import DefiniteClient


def main():
    """Main function demonstrating SQL functionality."""

    # Get API key from environment variable
    api_key = os.environ.get("DEFINITE_API_KEY")
    if not api_key:
        print("Error: DEFINITE_API_KEY environment variable is required")
        print(
            "You can find your API key in the bottom left user menu of your Definite workspace"
        )
        sys.exit(1)

    # Initialize the client
    client = DefiniteClient(api_key)
    sql_client = client.get_sql_client()

    print("🚀 Definite SDK SQL Example")
    print("=" * 40)

    # Example 1: Simple SQL query
    print("\n1. Executing a simple SQL query:")
    try:
        result = sql_client.execute("SELECT 1 as test_column")
        print(f"✅ Query executed successfully: {result}")
    except Exception as e:
        print(f"❌ Query failed: {e}")

    # Example 2: SQL query with integration ID
    print("\n2. Executing SQL query with integration ID:")
    integration_id = (
        "your_database_integration_id"  # Replace with actual integration ID
    )
    try:
        result = sql_client.execute(
            "SELECT COUNT(*) as row_count FROM information_schema.tables",
            integration_id=integration_id,
        )
        print(f"✅ Query executed successfully: {result}")
    except Exception as e:
        print(f"❌ Query failed: {e}")
        print(
            "💡 Make sure to replace 'your_database_integration_id' with your actual integration ID"
        )

    # Example 3: Cube query
    print("\n3. Executing a Cube query:")
    cube_query = {
        "dimensions": [],
        "measures": ["sales.total_amount"],
        "timeDimensions": [{"dimension": "sales.date", "granularity": "month"}],
        "limit": 10,
    }

    cube_integration_id = (
        "your_cube_integration_id"  # Replace with actual Cube integration ID
    )
    try:
        result = sql_client.execute_cube_query(
            cube_query, integration_id=cube_integration_id
        )
        print(f"✅ Cube query executed successfully: {result}")
    except Exception as e:
        print(f"❌ Cube query failed: {e}")
        print(
            "💡 Make sure to replace 'your_cube_integration_id' with your actual Cube integration ID"
        )

    # Example 4: Demonstrating other SDK features
    print("\n4. Other SDK features:")

    # Key-value store
    print("\n   📦 Key-Value Store:")
    try:
        store = client.get_kv_store("example_store")
        store["example_key"] = "example_value"
        print(f"   ✅ Stored value: {store['example_key']}")
    except Exception as e:
        print(f"   ❌ KV store operation failed: {e}")

    # List integrations
    print("\n   🔗 Integration Management:")
    try:
        integration_store = client.get_integration_store()
        integrations = list(integration_store.list_integrations())
        print(f"   ✅ Found {len(integrations)} integrations")
    except Exception as e:
        print(f"   ❌ Integration listing failed: {e}")

    print("\n🎉 Example completed!")
    print("\nNext steps:")
    print("- Replace the placeholder integration IDs with your actual integration IDs")
    print("- Modify the SQL queries to match your database schema")
    print(
        "- Check the Definite documentation for more advanced usage: https://docs.definite.app/"
    )


if __name__ == "__main__":
    main()
