import os
from typing import Optional

from definite_sdk.integration import DefiniteIntegrationStore
from definite_sdk.message import DefiniteMessageClient
from definite_sdk.secret import DefiniteSecretStore
from definite_sdk.sql import DefiniteSqlClient
from definite_sdk.store import DefiniteKVStore

API_URL = "https://api.definite.app"


class DefiniteClient:
    """Client for interacting with the Definite API."""

    def __init__(self, api_key: Optional[str] = None, api_url: str = API_URL):
        """Creates a definite client with the provided API key.

        Args:
            api_key: API key for authentication. If not provided, will look for
                    DEFINITE_API_KEY or DEF_API_KEY environment variables.
            api_url: Base URL for the Definite API.

        See: https://docs.definite.app/definite-api for how to obtain an API key.
        """
        if api_key is None:
            api_key = os.getenv("DEFINITE_API_KEY") or os.getenv("DEF_API_KEY")
            if not api_key:
                raise ValueError(
                    "API key must be provided or set in DEFINITE_API_KEY "
                    "or DEF_API_KEY environment variable"
                )

        self.api_key = api_key
        self.api_url = api_url

    def get_kv_store(self, name: str) -> DefiniteKVStore:
        """Initializes a key-value store with the provided name.

        See DefiniteKVStore for more how to interact with the store.
        """

        return DefiniteKVStore(name, self.api_key, self.api_url)

    def get_secret_store(self) -> DefiniteSecretStore:
        """Initializes the secret store.

        See DefiniteSecretStore for more how to interact with the store.
        """

        return DefiniteSecretStore(self.api_key, self.api_url)

    def get_integration_store(self) -> DefiniteIntegrationStore:
        """Initializes the integration store.

        See DefiniteIntegrationStore for more how to interact with the store.
        """

        return DefiniteIntegrationStore(self.api_key, self.api_url)

    def get_sql_client(self) -> DefiniteSqlClient:
        """Initializes the SQL client for executing SQL queries.

        See DefiniteSqlClient for more how to execute SQL queries.
        """

        return DefiniteSqlClient(self.api_key, self.api_url)

    def attach_ducklake(self, alias: str = "lake") -> str:
        """Generates SQL statements to attach DuckLake to a DuckDB connection.

        This method fetches the team's DuckLake integration credentials and generates
        the necessary SQL statements to create a GCS secret and attach DuckLake.


        Args:
            alias: The alias name for the attached DuckLake database (default: "lake")

        Returns:
            str: SQL statements to execute for attaching DuckLake

        Example:
            >>> client = DefiniteClient(os.environ["DEFINITE_API_KEY"])
            >>> sql = client.attach_ducklake()
            >>> conn.execute(sql)
        """
        # Fetch DuckLake integration details
        integrations_client = self.get_integration_store()
        integrations = integrations_client.list_integrations(
            integration_type="ducklake"
        )
        if len(integrations) == 0:
            raise Exception(
                "DuckLake integration not found. Please make sure one is"
                "created for your team at https://ui.definite.app/settings/integrations"
            )

        integration = integrations.pop()

        # Generate GCS secret SQL based on available credentials.
        # New integrations (April 2026+) use ADC / credential_chain instead
        # of HMAC keys. Legacy integrations may still have HMAC keys.
        gcs_access_key = integration.get("gcs_access_key_id")
        gcs_secret_key = integration.get("gcs_secret_access_key")
        service_account_key = integration.get("service_account_key")

        if gcs_access_key and gcs_secret_key:
            # Legacy: HMAC key-based auth
            create_secret_sql = f"""CREATE SECRET (
            TYPE gcs,
            KEY_ID '{gcs_access_key}',
            SECRET '{gcs_secret_key}'
        );"""
        elif service_account_key:
            # Service account JSON key
            import json

            sa_json = json.dumps(service_account_key).replace("'", "''")
            create_secret_sql = f"""CREATE SECRET (
            TYPE gcs,
            PROVIDER service_account,
            SERVICE_ACCOUNT_JSON '{sa_json}'
        );"""
        else:
            # ADC / credential_chain (GKE workload identity or local gcloud auth).
            # Locally, requires: gcloud auth application-default login
            create_secret_sql = """CREATE SECRET (
            TYPE gcs,
            PROVIDER credential_chain
        );"""
            import warnings

            warnings.warn(
                "DuckLake integration has no HMAC or service account keys. "
                "Using credential_chain (GCP Application Default Credentials). "
                "On GKE this works via Workload Identity. Locally, run: "
                "gcloud auth application-default login --project=definite-371419\n"
                "If attach fails, use client.get_sql_client().execute(sql) instead.",
                stacklevel=2,
            )

        # Build PostgreSQL connection string
        pg_conn_str = (
            f"postgresql://{integration['pg_user']}:"
            f"{integration['pg_password']}@"
            f"{integration['pg_host']}:"
            f"{integration['pg_port']}/"
            f"{integration['pg_database']}"
        )

        attach_sql = (
            f"ATTACH 'ducklake:postgres:{pg_conn_str}' AS {alias} "
            f"(DATA_PATH 'gs://{integration['gcs_bucket_path']}', "
            f"METADATA_SCHEMA '{integration['pg_schema']}');"
        )

        return f"{create_secret_sql}\n\n{attach_sql}"

    # Alias methods for consistency
    def kv_store(self, name: str) -> DefiniteKVStore:
        """Alias for get_kv_store."""
        return self.get_kv_store(name)

    def secret_store(self) -> DefiniteSecretStore:
        """Alias for get_secret_store."""
        return self.get_secret_store()

    def integration_store(self) -> DefiniteIntegrationStore:
        """Alias for get_integration_store."""
        return self.get_integration_store()

    def get_message_client(self) -> DefiniteMessageClient:
        """Initializes the message client for sending messages via various channels.

        See DefiniteMessageClient for more how to send messages.
        """

        return DefiniteMessageClient(self.api_key, self.api_url)

    def message_client(self) -> DefiniteMessageClient:
        """Alias for get_message_client."""
        return self.get_message_client()
