"""
Example demonstrating how to use the attach_ducklake() method 
to connect to your team's DuckLake from DuckDB.
"""

import os
import duckdb
import pandas as pd
from definite_sdk import DefiniteClient


def main():
    """Example usage of DuckLake integration."""
    
    # Initialize the Definite client
    api_key = os.environ.get("DEFINITE_API_KEY")
    if not api_key:
        print("Please set DEFINITE_API_KEY environment variable")
        return
    
    client = DefiniteClient(api_key)
    
    # Connect to DuckDB
    conn = duckdb.connect()
    
    try:
        # Attach DuckLake to the DuckDB connection
        print("Attaching DuckLake...")
        attach_sql = client.attach_ducklake()
        print("Generated SQL:")
        print(attach_sql)
        print("\nExecuting attachment...")
        
        conn.execute(attach_sql)
        print("✅ DuckLake attached successfully!")
        
        # Create some sample data
        sample_data = pd.DataFrame([
            {'id': '123', 'name': 'brian', 'department': 'engineering'},
            {'id': 'abc', 'name': 'steven', 'department': 'product'},
            {'id': 'def', 'name': 'alice', 'department': 'design'}
        ])
        
        # Create a schema and table in DuckLake
        print("\nCreating sample data in DuckLake...")
        conn.execute("CREATE SCHEMA IF NOT EXISTS lake.example;")
        conn.execute("""
            CREATE OR REPLACE TABLE lake.example.users AS 
            SELECT * FROM sample_data
        """)
        print("✅ Sample table created!")
        
        # Query the data back
        print("\nQuerying data from DuckLake:")
        result = conn.sql("SELECT * FROM lake.example.users").df()
        print(result)
        
        # Show available schemas in DuckLake
        print("\nAvailable schemas in DuckLake:")
        schemas = conn.sql("SHOW SCHEMAS FROM lake").df()
        print(schemas)
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        conn.close()


def custom_alias_example():
    """Example using a custom alias for DuckLake."""
    
    api_key = os.environ.get("DEFINITE_API_KEY")
    if not api_key:
        print("Please set DEFINITE_API_KEY environment variable")
        return
        
    client = DefiniteClient(api_key)
    conn = duckdb.connect()
    
    try:
        # Attach DuckLake with custom alias
        print("Attaching DuckLake with custom alias 'warehouse'...")
        attach_sql = client.attach_ducklake(alias="warehouse")
        conn.execute(attach_sql)
        print("✅ DuckLake attached as 'warehouse'!")
        
        # Use the custom alias
        conn.execute("CREATE SCHEMA IF NOT EXISTS warehouse.analytics;")
        print("✅ Created schema using custom alias!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        conn.close()


if __name__ == "__main__":
    print("=== DuckLake Integration Example ===")
    main()
    
    print("\n=== Custom Alias Example ===")
    custom_alias_example() 