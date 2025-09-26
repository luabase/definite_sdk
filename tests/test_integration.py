import os

from definite_sdk.client import DefiniteClient, API_URL

api_key = os.getenv("DEF_API_KEY") or ""
api_url = os.getenv("DEF_API_URL") or API_URL


def test_integration_store():
    integration_store = DefiniteClient(api_key, api_url).get_integration_store()

    integrations = list(integration_store.list_integrations())
    assert len(list(integrations)) > 0

    # Test get_integration by name
    integration = integration_store.get_integration(integrations[0]["name"])
    assert integration is not None


def test_get_integration_by_id():
    """
    Test get_integration_by_id method.

    Note: This test uses a mock integration ID since the list_integrations endpoint
    doesn't return integration IDs. In practice, integration IDs would come from
    other API endpoints or be provided by users.
    """
    integration_store = DefiniteClient(api_key, api_url).get_integration_store()

    # Test with a non-existent integration ID to verify the method works
    # (we expect this to fail with a 404, which confirms the endpoint is called correctly)
    try:
        integration_store.get_integration_by_id("00000000-0000-0000-0000-000000000000")
        assert False, "Expected an exception for non-existent integration ID"
    except Exception as e:
        # We expect a 404 or similar error, which confirms the method is working
        assert "not found" in str(e).lower()
