import os
from typing import Optional

from definite_sdk.integration import DefiniteIntegrationStore
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
