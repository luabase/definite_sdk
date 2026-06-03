"""
Example demonstrating the recommended way to write data into the Definite data
lake: upload a file to Definite Drive, then run SQL that reads it into a
``LAKE.<schema>.<table>`` table.

This Drive + SQL workflow works for all teams, including workload-identity-only
teams provisioned after April 2026 (for which the legacy ``attach_ducklake()``
helper raises ``UnsupportedDuckLakeAttachError``). See examples/ducklake_example.py
for the deprecated local-DuckDB approach.
"""

import io
import os

import pandas as pd

from definite_sdk import DefiniteClient

SCHEMA = "example"
TABLE = f"LAKE.{SCHEMA}.users"


def main():
    """Create, append to, and upsert into a data lake table via Drive + SQL."""

    api_key = os.environ.get("DEFINITE_API_KEY")
    if not api_key:
        print("Please set DEFINITE_API_KEY environment variable")
        return

    client = DefiniteClient(api_key)
    drive = client.get_drive_client()
    sql = client.get_sql_client()

    def upload(df: pd.DataFrame, name: str) -> str:
        """Serialize a DataFrame to parquet and upload it to Drive; return its gcs_path."""
        buf = io.BytesIO()
        df.to_parquet(buf)
        result = drive.write_temporary_file(buf.getvalue(), name=name, ttl_days=1)
        print(f"   uploaded {name} -> {result.gcs_path}")
        return result.gcs_path

    try:
        # 1. CREATE (or replace) the table from an uploaded parquet file
        print("Creating table via CREATE OR REPLACE ...")
        initial = pd.DataFrame(
            [
                {"id": 1, "name": "alice", "department": "engineering"},
                {"id": 2, "name": "bob", "department": "product"},
            ]
        )
        gcs_path = upload(initial, "users_initial.parquet")
        sql.execute(
            f"CREATE OR REPLACE TABLE {TABLE} AS "
            f"SELECT * FROM read_parquet('{gcs_path}')"
        )
        print("✅ Table created")

        # 2. INSERT (append) more rows
        print("\nAppending rows via INSERT INTO ...")
        more = pd.DataFrame([{"id": 3, "name": "carol", "department": "design"}])
        gcs_path = upload(more, "users_append.parquet")
        sql.execute(
            f"INSERT INTO {TABLE} SELECT * FROM read_parquet('{gcs_path}')"
        )
        print("✅ Rows appended")

        # 3. MERGE / upsert on the `id` key (update existing, insert new)
        print("\nUpserting rows via MERGE INTO ...")
        changes = pd.DataFrame(
            [
                {"id": 2, "name": "bob", "department": "growth"},  # update
                {"id": 4, "name": "dave", "department": "sales"},  # insert
            ]
        )
        gcs_path = upload(changes, "users_merge.parquet")
        sql.execute(
            f"""
            MERGE INTO {TABLE} AS t
            USING (SELECT * FROM read_parquet('{gcs_path}')) AS s
            ON t.id = s.id
            WHEN MATCHED THEN UPDATE SET *
            WHEN NOT MATCHED THEN INSERT *
            """
        )
        print("✅ Rows upserted")

        # 4. Read the result back
        print("\nReading the table back:")
        result = sql.execute(f"SELECT * FROM {TABLE} ORDER BY id")
        for row in result.get("data", []):
            print(f"   {row}")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("=== Data Lake Write Example (Drive + SQL) ===")
    main()
