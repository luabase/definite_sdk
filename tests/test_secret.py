import os

import pytest

from definite_sdk.client import DefiniteClient

api_key = os.environ.get("DEF_API_KEY") or ""

assert api_key


def test_secret_store():
    secret_store = DefiniteClient(
        api_key,
    ).get_secret_store()

    secret_store.set_secret("key", "value")

    assert secret_store.get_secret("key") == "value"
    assert "key" in list(secret_store.list_secrets())

    secret_store.delete_secret("key")

    with pytest.raises(Exception):
        secret_store.get_secret("key")
    assert "key" not in list(secret_store.list_secrets())
