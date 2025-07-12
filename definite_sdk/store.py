from typing import Iterator, Union, Optional

import requests

STORE_ENDPOINT = "/v1/store"


class DefiniteKVStore:
    """
    A key-value store hosted by Definite.

    Initialization:
    >>> client = DefiniteSdkClient("MY_API_KEY")
    >>> store = client.get_kv_store("my_store")

    Accessing values:
    >>> print(store["key"])

    Setting values:
    >>> store["key"] = "value"
    >>> store.commit()

    To permanently delete "my_store":
    >>> store.delete()

    You MUST call commit() to save changes to the store.

    The store uses versioning to prevent conflicts/stomping. If the store has
    been modified since you last loaded it, the commit will fail.
    """

    def __init__(self, name: str, api_key: str, api_url: str):
        """
        Initializes the DefiniteKVStore with the provided name and API key.

        Args:
            name (str): The name of the key-value store.
            api_key (str): The API key for authorization.

        Raises:
            Exception: If the store fails to load.
        """

        self._api_key = api_key
        self._name = name
        self._store_url = api_url + STORE_ENDPOINT
        response = requests.get(
            self._store_url + f"/{name}",
            headers={"Authorization": "Bearer " + self._api_key},
        )

        if response.status_code == 404:
            # Store not found. Create a new one.
            self._data = {}
            self._version_id = None
        elif response.status_code == 200:
            # Store found. Load the data.
            response_json = response.json()
            self._data = response_json["data"]
            self._version_id = response_json["version_id"]
        else:
            raise Exception("Failed to load the store: " + response.text)

    def commit(self):
        """
        Commits the current state of the store to the remote server.

        Raises:
            Exception: If the commit fails.

        Example:
            store.commit()
        """
        response = requests.post(
            self._store_url,
            json={
                "name": self._name,
                "data": self._data,
                "existing_version_id": self._version_id,
            },
            headers={"Authorization": "Bearer " + self._api_key},
        )

        if response.status_code != 200:
            raise Exception("Failed to commit the DefiniteKVStore: " + response.text)
        else:
            response_json = response.json()
            self._version_id = response_json.get("version_id")

    def delete(self):
        """
        Deletes the store from the remote server.

        Raises:
            Exception: If the delete fails.

        Example:
            store.delete()
        """
        response = requests.delete(
            self._store_url,
            json={"name": self._name},
            headers={"Authorization": "Bearer " + self._api_key},
        )

        if response.status_code != 200:
            raise Exception("Failed to delete the DefiniteKVStore: " + response.text)

        self._data = {}
        self._version_id = None

    def __getitem__(self, key: str) -> Optional[str]:
        """
        Gets the value for a given key.

        Args:
            key (str): The key to retrieve the value for.

        Returns:
            The value associated with the key, or None if the key does not exist.

        Example:
            value = store["key1"]
        """
        return self._data.get(key)

    def __setitem__(self, key: str, value: str):
        """
        Sets a key-value pair in the store.

        Args:
            key (str): The key to set.
            value (str): The value to set.

        Raises:
            AssertionError: If key or value is not a string.

        Example:
            store["key1"] = "value1"
        """
        assert isinstance(key, str)
        assert isinstance(value, str)
        self._data[key] = value

    def __delitem__(self, key: str) -> None:
        """
        Deletes a key-value pair from the store.

        Args:
            key (str): The key to delete.

        Example:
            del store["key1"]
        """
        del self._data[key]

    def __iter__(self) -> Iterator[str]:
        """
        Returns an iterator over the keys in the store.

        Returns:
            An iterator over the keys in the store.

        Example:
            for key in store:
                print(key)
        """
        return iter(self._data)

    def __len__(self) -> int:
        """
        Returns the number of key-value pairs in the store.

        Returns:
            The number of key-value pairs in the store.

        Example:
            length = len(store)
        """
        return len(self._data)

    def __repr__(self) -> str:
        """
        Returns a string representation of the store, similar to a dictionary.

        Returns:
            A string representation of the store.

        Example:
            print(store)
        """
        return repr(self._data)

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Gets the value for a given key with a default.

        Args:
            key (str): The key to retrieve the value for.
            default: The default value to return if key doesn't exist.

        Returns:
            The value associated with the key, or default if the key does not exist.

        Example:
            value = store.get("key1", "default_value")
        """
        return self._data.get(key, default)
