import os
from typing import Optional

from definite_sdk.drive import DefiniteDriveClient
from definite_sdk.integration import DefiniteIntegrationStore
from definite_sdk.message import DefiniteMessageClient
from definite_sdk.secret import DefiniteSecretStore
from definite_sdk.sql import DefiniteSqlClient
from definite_sdk.store import DefiniteKVStore

API_URL = "https://api.definite.app"


class UnsupportedDuckLakeAttachError(Exception):
    """Raised when attach_ducklake() cannot produce usable credentials.

    Teams provisioned after April 2026 use workload-identity-only auth for
    DuckLake (no HMAC keys or service account JSON stored on the integration),
    which cannot be replicated on a customer laptop. Use the Drive + SQL
    workflow instead:

        drive = client.get_drive_client()
        sql = client.get_sql_client()
        r = drive.write_temporary_file(data, name="events.parquet")
        sql.execute(
            f"CREATE TABLE LAKE.MY_SCHEMA.events AS "
            f"SELECT * FROM read_parquet('{r.gcs_path}')"
        )
    """


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

    def get_drive_client(self) -> DefiniteDriveClient:
        """Initializes the Drive client for writing files to Definite Drive.

        See DefiniteDriveClient for how to write files and temporary files.
        """

        return DefiniteDriveClient(self.api_key, self.api_url)

    def attach_ducklake(self, alias: str = "lake") -> str:
        """Generate SQL statements to attach DuckLake to a local DuckDB connection.

        .. deprecated::
            This method is deprecated and will be removed in a future release.
            It only works for teams with legacy HMAC keys or service account JSON
            on their DuckLake integration. Teams provisioned after April 2026 use
            workload-identity-only auth and will raise :class:`UnsupportedDuckLakeAttachError`.

            Use the Drive + SQL workflow instead:

            >>> drive = client.get_drive_client()
            >>> sql = client.get_sql_client()
            >>> r = drive.write_temporary_file(data, name="events.parquet")
            >>> sql.execute(
            ...     f"CREATE TABLE LAKE.MY_SCHEMA.events AS "
            ...     f"SELECT * FROM read_parquet('{r.gcs_path}')"
            ... )

        Args:
            alias: The alias name for the attached DuckLake database (default: "lake")

        Returns:
            str: SQL statements to execute for attaching DuckLake

        Raises:
            UnsupportedDuckLakeAttachError: When the team's DuckLake integration has
                neither HMAC keys nor a service account JSON (i.e. workload-identity-only
                teams, where local attach is not possible).
        """
        import warnings

        warnings.warn(
            "attach_ducklake() is deprecated and will be removed in a future "
            "release. Use DefiniteClient.get_drive_client().write_temporary_file(...) "
            "to upload local data, then DefiniteClient.get_sql_client().execute(...) "
            "to run `CREATE TABLE ... AS SELECT * FROM read_parquet('{gcs_path}')` "
            "against DuckLake. See https://docs.definite.app for details.",
            DeprecationWarning,
            stacklevel=2,
        )

        # Fetch DuckLake integration details
        integrations_client = self.get_integration_store()
        integrations = integrations_client.list_integrations(integration_type="ducklake")
        if len(integrations) == 0:
            raise Exception(
                "DuckLake integration not found. Please make sure one is "
                "created for your team at https://ui.definite.app/settings/integrations"
            )

        integration = integrations.pop()

        # Generate GCS secret SQL based on available credentials.
        # - Legacy teams: HMAC keys populated (gcs_access_key_id / gcs_secret_access_key).
        # - Some teams: service-account JSON populated. The backend serializes this
        #   under the alias `serviceAccountKey` (camelCase) for historical reasons,
        #   but `service_account_key` is the field's canonical name — accept both.
        # - Post-April-2026 teams: none of the above; workload-identity-only.
        gcs_access_key = integration.get("gcs_access_key_id")
        gcs_secret_key = integration.get("gcs_secret_access_key")
        service_account_key = integration.get("service_account_key") or integration.get("serviceAccountKey")

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
            raise UnsupportedDuckLakeAttachError(
                "This team's DuckLake integration has no HMAC keys or service "
                "account JSON — it uses workload-identity-only auth, which cannot "
                "be used from a customer laptop. Use the Drive + SQL workflow "
                "instead:\n\n"
                "    drive = client.get_drive_client()\n"
                "    sql = client.get_sql_client()\n"
                "    r = drive.write_temporary_file(data, name='events.parquet')\n"
                "    sql.execute(\n"
                "        f\"CREATE TABLE LAKE.MY_SCHEMA.events AS \"\n"
                "        f\"SELECT * FROM read_parquet('{r.gcs_path}')\"\n"
                "    )\n"
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

    def drive_client(self) -> DefiniteDriveClient:
        """Alias for get_drive_client."""
        return self.get_drive_client()
