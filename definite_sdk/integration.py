from typing import Dict, List, cast

import requests

INTEGRATION_ENDPOINT = "/v1/api/integrations"


class DefiniteIntegrationStore:
    """
    Read only access to the integration store on Definite.

    Initialization:
    >>> client = DefiniteSdkClient("MY_API_KEY")
    >>> integration_store = client.get_integration_store()

    Accessing values:
    >>> integration_store.list_integrations()
    >>> integration_store.get_integration("name")
    >>> integration_store.get_integration_by_id("integration_id")
    """

    def __init__(self, api_key: str, api_url: str):
        """
        Initializes the DefiniteSecretStore

        Args:
            api_key (str): The API key for authorization.
        """
        self._api_key = api_key
        self._integrations_url = api_url + INTEGRATION_ENDPOINT

    def list_integrations(self) -> List[Dict]:
        """
        Lists all integrations in the store.

        Returns:
            Iterator[str]: An iterator of integrations.
        """
        response = requests.get(
            self._integrations_url,
            params={"category": "extractor"},
            headers={"Authorization": "Bearer " + self._api_key},
        )
        response.raise_for_status()
        cursor_page = response.json()
        integrations = cursor_page.get("data", [])
        details = [i.get("details", {}) for i in integrations]
        return cast(List[Dict], details)

    def get_integration(self, name: str) -> Dict:
        """
        Retrieves an integration by name.

        Args:
            name (str): The name of the integration.

        Returns:
            str: The value of the integration.
        """
        response = requests.get(
            self._integrations_url,
            params={"name": name, "limit": 1},
            headers={"Authorization": "Bearer " + self._api_key},
        )
        response.raise_for_status()
        cursor_page = response.json()
        integrations = cursor_page.get("data", [])
        if len(integrations) == 0:
            raise Exception(f"Integration with name {name} not found")
        integration = integrations[0]
        return integration.get("details", {})

    def get_integration_by_id(self, integration_id: str) -> Dict:
        """
        Retrieves an integration by ID.

        Args:
            integration_id (str): The ID of the integration.

        Returns:
            dict: The integration details.
        """
        response = requests.get(
            self._integrations_url,
            params={"id": integration_id, "limit": 1},
            headers={"Authorization": "Bearer " + self._api_key},
        )
        response.raise_for_status()
        cursor_page = response.json()
        integrations = cursor_page.get("data", [])
        if len(integrations) == 0:
            raise Exception(f"Integration with ID {integration_id} not found")
        integration = integrations[0]
        return integration.get("details", {})

    def lookup_duckdb_integration(self) -> Dict:
        """
        Look up the team's DuckDB integration.

        Returns:
            Optional[Tuple[str, str]]: Tuple of (integration_id, connection_uri)
                if found, None if no DuckDB integration exists.
        """
        response = requests.get(
            self._integrations_url,
            params={"type": "duckdb", "limit": 1},
            headers={"Authorization": "Bearer " + self._api_key},
        )
        response.raise_for_status()
        cursor_page = response.json()
        integrations = cursor_page.get("data", [])
        if len(integrations) == 0:
            raise Exception("Integration with type `duckdb` not found")
        integration = integrations[0]
        return integration.get("details", {})
