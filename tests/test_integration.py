import os

import pytest
import requests

from definite_sdk.client import DefiniteClient, API_URL

api_key = os.getenv("DEF_API_KEY") or ""
api_url = os.getenv("DEF_API_URL") or API_URL


def get_first_integration_id():
    """Helper to get an integration ID for testing."""
    response = requests.get(
        f"{api_url}/v1/api/integrations",
        params={"limit": 1},
        headers={"Authorization": f"Bearer {api_key}"},
    )
    response.raise_for_status()
    integrations = response.json().get("data", [])
    return integrations[0]["id"] if integrations else None


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


def test_get_syncs():
    """Test get_syncs method with a valid integration."""
    integration_id = get_first_integration_id()
    if not integration_id:
        pytest.skip("No integrations available for testing")

    integration_store = DefiniteClient(api_key, api_url).get_integration_store()
    syncs = integration_store.get_syncs(integration_id)

    assert isinstance(syncs, list)
    # If there are syncs, verify structure
    if syncs:
        sync = syncs[0]
        assert "dag_name" in sync
        assert "run_id" in sync
        assert "status" in sync


def test_get_syncs_with_pagination():
    """Test get_syncs method with pagination parameters."""
    integration_id = get_first_integration_id()
    if not integration_id:
        pytest.skip("No integrations available for testing")

    integration_store = DefiniteClient(api_key, api_url).get_integration_store()
    syncs = integration_store.get_syncs(integration_id, limit=10, offset=0, desc=True)

    assert isinstance(syncs, list)
    assert len(syncs) <= 10


def test_get_syncs_invalid_integration():
    """Test get_syncs with non-existent integration ID."""
    integration_store = DefiniteClient(api_key, api_url).get_integration_store()

    try:
        integration_store.get_syncs("00000000-0000-0000-0000-000000000000")
        assert False, "Expected an exception for non-existent integration"
    except Exception as e:
        assert "404" in str(e) or "not found" in str(e).lower()


def test_get_latest_sync():
    """Test get_latest_sync convenience method."""
    integration_id = get_first_integration_id()
    if not integration_id:
        pytest.skip("No integrations available for testing")

    integration_store = DefiniteClient(api_key, api_url).get_integration_store()
    latest = integration_store.get_latest_sync(integration_id)

    # Should return either a dict or None
    assert latest is None or isinstance(latest, dict)
