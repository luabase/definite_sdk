from typing import Iterator

import requests

SECRET_STORE_ENDPOINT = "/v1/api/integration"


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
        self._integration_store_url = api_url + SECRET_STORE_ENDPOINT
    
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
        return response.json()
