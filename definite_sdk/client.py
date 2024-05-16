from store import DefiniteKVStore

API_URL = "https://api.definite.app"


class DefiniteClient:
    """Client for interacting with the Definite API."""

    def __init__(self, api_key: str, api_url: str = API_URL):
        """Creates a definite client with the provided API key.

        See: https://docs.definite.app/definite-api for how to obtain an API key.
        """
        self.api_key = api_key
        self.api_url = api_url

    def get_kv_store(self, name: str) -> DefiniteKVStore:
        """Initializes a key-value store with the provided name.

        See DefiniteKVStore for more how to interact with the store.
        """

        return DefiniteKVStore(name, self.api_key, self.api_url)
