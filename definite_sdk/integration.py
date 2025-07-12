from typing import Iterator, Optional, Tuple

import requests

INTEGRATION_ENDPOINT = "/v1/api/integration"


class DefiniteIntegrationStore:
    """
    Read only access to the integration store on Definite.

    Initialization:
    >>> client = DefiniteSdkClient("MY_API_KEY")
    >>> integration_store = client.get_integration_store()

    Accessing values:
    >>> integration_store.list_integrations()
    >>> integration_store.get_integration("name")
    """

    def __init__(self, api_key: str, api_url: str):
        """
        Initializes the DefiniteSecretStore

        Args:
            api_key (str): The API key for authorization.
        """
        self._api_key = api_key
        self._integration_store_url = api_url + INTEGRATION_ENDPOINT

    def list_integrations(self) -> Iterator[dict]:
        """
        Lists all integrations in the store.

        Returns:
            Iterator[str]: An iterator of integrations.
        """
        response = requests.get(
            self._integration_store_url,
            headers={"Authorization": "Bearer " + self._api_key},
        )
        response.raise_for_status()
        return iter(response.json())

    def get_integration(self, name: str) -> dict:
        """
        Retrieves an integration by name.

        Args:
            name (str): The name of the integration.

        Returns:
            str: The value of the integration.
        """
        response = requests.get(
            self._integration_store_url + f"/{name}",
            headers={"Authorization": "Bearer " + self._api_key},
        )
        response.raise_for_status()
        return dict(response.json())

    def lookup_duckdb_integration(self) -> Optional[Tuple[str, str]]:
        """
        Look up the team's DuckDB integration.
        
        Note: Currently, the API only returns extractor (source) integrations.
        Destination integrations like DuckDB are not yet exposed through this endpoint.
        This method is provided for future compatibility when the API is updated.

        Returns:
            Optional[Tuple[str, str]]: Tuple of (integration_id, connection_uri)
                if found, None if no DuckDB integration exists.
        """
        try:
            response = requests.get(
                self._integration_store_url,
                headers={"Authorization": "Bearer " + self._api_key},
            )
            response.raise_for_status()
            integrations = response.json()
        except:
            return None

        # Check for DuckDB in the integrations
        # Note: Currently this will not find DuckDB as it's a destination integration
        for integration in integrations:
            integration_type = integration.get("integration_type", "").lower()
            if integration_type == "duckdb" and integration.get("active", True):
                integration_id = integration.get("id")
                # Connection URI might be in config or connection_string field
                connection_uri = (
                    integration.get("connection_string")
                    or integration.get("config", {}).get("database_path")
                    or integration.get("config", {}).get("connection_string")
                )
                if integration_id and connection_uri:
                    return (integration_id, connection_uri)

        return None
