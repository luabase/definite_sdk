import os


from definite_sdk.client import DefiniteClient, API_URL

api_key = os.getenv("DEF_API_KEY") or ""
api_url = os.getenv("DEF_API_URL") or API_URL


def test_attach_ducklake():
    client = DefiniteClient(api_key, api_url)
    stmt = client.attach_ducklake()
    assert "CREATE SECRET" in stmt
    assert "TYPE gcs" in stmt
    assert "KEY_ID" in stmt
    assert "ATTACH" in stmt
