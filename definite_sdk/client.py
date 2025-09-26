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

        # Generate SQL statements
        create_secret_sql = f"""CREATE SECRET (
            TYPE gcs,
            KEY_ID '{integration["gcs_access_key_id"]}',
            SECRET '{integration["gcs_secret_access_key"]}'
        );"""

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
