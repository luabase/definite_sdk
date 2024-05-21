import os

from definite_sdk.client import DefiniteClient

api_key = os.environ.get("DEF_API_KEY") or ""

assert api_key


def test_integration_store():
    integration_store = DefiniteClient(
        api_key,
    ).get_integration_store()

    integrations = list(integration_store.list_integrations())
    assert len(list(integrations)) > 0

    integration = integration_store.get_integration(integrations[0]["name"])
    assert integration is not None
