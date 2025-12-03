from typing import Dict, List, Optional, cast

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

    def list_integrations(
        self,
        *,
        integration_type: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[Dict]:
        """
        Lists all integrations in the store.

        Args:
            integration_type (str): Optional type filter
            category (str): Optional category filter

        Returns:
            Iterator[str]: An iterator of integrations.
        """
        params = {}
        if integration_type:
            params |= {"type": integration_type}
        if category:
            params |= {"category": category}

        response = requests.get(
            self._integrations_url,
            params=params,
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

    def get_syncs(
        self,
        integration_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
        desc: bool = True,
        status: Optional[str] = None,
    ) -> List[Dict]:
        """
        Retrieves sync runs (DAG runs) for an integration.

        Args:
            integration_id (str): The ID of the integration.
            limit (int): Maximum number of results to return (default: 50, max: 100).
            offset (int): Number of results to skip for pagination (default: 0).
            desc (bool): Sort by created_at descending if True (default: True).
            status (str): Optional filter by status ("STARTED", "SUCCESS", "FAILED").

        Returns:
            List[Dict]: List of DAG run records with keys:
                - dag_name: Name of the DAG
                - run_id: Unique ID for this run
                - created_at: ISO datetime when created
                - updated_at: ISO datetime when updated
                - src_integration_id: Source integration UUID
                - dst_integration_id: Destination integration UUID
                - status: Run status (STARTED, SUCCESS, FAILED)
                - details: Additional run details
        """
        params: Dict = {
            "limit": limit,
            "offset": offset,
            "desc": str(desc).lower(),
        }
        if status:
            params["status"] = status

        response = requests.get(
            f"{self._integrations_url}/{integration_id}/syncs",
            params=params,
            headers={"Authorization": "Bearer " + self._api_key},
        )
        response.raise_for_status()
        cursor_page = response.json()
        return cast(List[Dict], cursor_page.get("data", []))

    def get_latest_sync(self, integration_id: str) -> Optional[Dict]:
        """
        Retrieves the most recent sync run for an integration.

        Args:
            integration_id (str): The ID of the integration.

        Returns:
            Optional[Dict]: The most recent DAG run, or None if no syncs exist.
        """
        syncs = self.get_syncs(integration_id, limit=1, desc=True)
        return syncs[0] if syncs else None
