import os

import pytest

from definite_sdk.client import DefiniteClient

api_key = os.environ.get("DEF_API_KEY") or ""

assert api_key


def test_store():
    def_store_1 = DefiniteClient(
        api_key,
    ).get_kv_store("definite_sdk_test_store")

    # Cleanup existing store, if it exists, for new test.
    def_store_1.delete()

    assert def_store_1["key"] is None

    # Data is visible before and after commit
    def_store_1["key"] = "value"
    assert def_store_1["key"] == "value"
    def_store_1.commit()
    assert def_store_1["key"] == "value"
    assert len(def_store_1) == 1

    # Commits are persisted across sessions
    def_store_2 = DefiniteClient(
        api_key,
    ).get_kv_store("definite_sdk_test_store")
    assert def_store_2["key"] == "value"

    # Commits from conflicting store throws exception
    def_store_2["store2_key"] = "store2_value"
    def_store_2.commit()

    with pytest.raises(Exception):
        def_store_1.commit()

    # Cleanup store.
    def_store_2.delete()
