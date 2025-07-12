from typing import Iterator

import requests

SECRET_STORE_ENDPOINT = "/v1/api/secret"


class DefiniteSecretStore:
    """
    A secret store hosted by Definite.

    Initialization:
    >>> client = DefiniteSdkClient("MY_API_KEY")
    >>> secret_store = client.get_secret_store()

    Accessing values:
    >>> secret_store.list_secrets()
    >>> secret_store.get_secret("key")

    Setting values:
    >>> secret_store.set_secret("key", "value")

    To permanently delete a secret:
    >>> secret_store.delete_secret("key")
    """

    def __init__(self, api_key: str, api_url: str):
        """
        Initializes the DefiniteSecretStore

        Args:
            api_key (str): The API key for authorization.
        """
        self._api_key = api_key
        self._secret_store_url = api_url + SECRET_STORE_ENDPOINT

    def list_secrets(self) -> Iterator[str]:
        """
        Lists all secrets in the store.

        Returns:
            Iterator[str]: An iterator of secret keys.
        """
        response = requests.get(
            self._secret_store_url,
            headers={"Authorization": "Bearer " + self._api_key},
        )
        response.raise_for_status()
        return iter(response.json()["secrets"])

    def get_secret(self, key: str) -> str:
        """
        Retrieves the value of a secret.

        Args:
            key (str): The key of the secret.

        Returns:
            str: The value of the secret.
        """
        response = requests.get(
            self._secret_store_url + f"/{key}",
            headers={"Authorization": "Bearer " + self._api_key},
        )
        response.raise_for_status()
        return str(response.json()["value"])

    def set_secret(self, key: str, value: str):
        """
        Sets the value of a secret.

        Args:
            key (str): The key of the secret.
            value (str): The value of the secret.
        """
        response = requests.post(
            self._secret_store_url + f"/{key}",
            json={"value": value},
            headers={"Authorization": "Bearer " + self._api_key},
        )
        response.raise_for_status()

    def delete_secret(self, key: str):
        """
        Deletes a secret.

        Args:
            key (str): The key of the secret.
        """
        response = requests.delete(
            self._secret_store_url + f"/{key}",
            headers={"Authorization": "Bearer " + self._api_key},
        )
        response.raise_for_status()
