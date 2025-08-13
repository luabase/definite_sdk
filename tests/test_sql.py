import os
from unittest.mock import Mock, patch

import pytest
import requests

from definite_sdk.client import DefiniteClient
from definite_sdk.sql import DefiniteSqlClient

# Mock API key for testing
TEST_API_KEY = "test_api_key"


class TestDefiniteSqlClient:
    """Test cases for the DefiniteSqlClient class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = DefiniteClient(TEST_API_KEY)
        self.sql_client = self.client.get_sql_client()

    def test_sql_client_initialization(self):
        """Test that SQL client is properly initialized."""
        assert isinstance(self.sql_client, DefiniteSqlClient)
        assert self.sql_client._api_key == TEST_API_KEY
        assert self.sql_client._sql_url == "https://api.definite.app/v1/query"

    @patch("definite_sdk.sql.requests.post")
    def test_execute_sql_without_integration_id(self, mock_post):
        """Test executing SQL query without integration ID."""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [{"count": 10}],
            "columns": ["count"],
            "success": True,
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Execute query
        result = self.sql_client.execute("SELECT COUNT(*) as count FROM users")

        # Verify the request
        mock_post.assert_called_once_with(
            "https://api.definite.app/v1/query",
            json={"sql": "SELECT COUNT(*) as count FROM users"},
            headers={"Authorization": "Bearer test_api_key"},
        )

        # Verify the result
        assert result["success"] is True
        assert result["data"] == [{"count": 10}]

    @patch("definite_sdk.sql.requests.post")
    def test_execute_sql_with_integration_id(self, mock_post):
        """Test executing SQL query with integration ID."""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [{"id": 1, "name": "John"}],
            "columns": ["id", "name"],
            "success": True,
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Execute query
        result = self.sql_client.execute(
            "SELECT id, name FROM users LIMIT 1", integration_id="my_db_integration"
        )

        # Verify the request
        mock_post.assert_called_once_with(
            "https://api.definite.app/v1/query",
            json={
                "sql": "SELECT id, name FROM users LIMIT 1",
                "integration_id": "my_db_integration",
            },
            headers={"Authorization": "Bearer test_api_key"},
        )

        # Verify the result
        assert result["success"] is True
        assert result["data"] == [{"id": 1, "name": "John"}]

    @patch("definite_sdk.sql.requests.post")
    def test_execute_cube_query_without_integration_id(self, mock_post):
        """Test executing Cube query without integration ID."""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [{"sales.total_amount": 50000}],
            "success": True,
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Prepare cube query
        cube_query = {
            "dimensions": [],
            "measures": ["sales.total_amount"],
            "timeDimensions": [{"dimension": "sales.date", "granularity": "month"}],
            "limit": 1000,
        }

        # Execute query
        result = self.sql_client.execute_cube_query(cube_query)

        # Verify the request
        mock_post.assert_called_once_with(
            "https://api.definite.app/v1/query",
            json={"cube_query": cube_query, "persist": True},
            headers={"Authorization": "Bearer test_api_key"},
        )

        # Verify the result
        assert result["success"] is True
        assert result["data"] == [{"sales.total_amount": 50000}]

    @patch("definite_sdk.sql.requests.post")
    def test_execute_cube_query_with_integration_id(self, mock_post):
        """Test executing Cube query with integration ID."""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [{"deals.win_rate": 0.85}],
            "success": True,
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Prepare cube query
        cube_query = {
            "dimensions": [],
            "measures": ["deals.win_rate"],
            "timeDimensions": [
                {"dimension": "deals.close_date", "granularity": "month"}
            ],
            "limit": 2000,
        }

        # Execute query
        result = self.sql_client.execute_cube_query(
            cube_query, integration_id="my_cube_integration"
        )

        # Verify the request
        mock_post.assert_called_once_with(
            "https://api.definite.app/v1/query",
            json={
                "cube_query": cube_query,
                "integration_id": "my_cube_integration",
                "persist": True,
            },
            headers={"Authorization": "Bearer test_api_key"},
        )

        # Verify the result
        assert result["success"] is True
        assert result["data"] == [{"deals.win_rate": 0.85}]

    @patch("definite_sdk.sql.requests.post")
    def test_execute_cube_query_with_raw_parameter(self, mock_post):
        """Test executing Cube query with raw parameter."""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            "raw_data": [{"value": 100}],
            "success": True,
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Prepare cube query
        cube_query = {
            "dimensions": [],
            "measures": ["sales.total_amount"],
            "limit": 1000,
        }

        # Execute query with raw=True
        result = self.sql_client.execute_cube_query(
            cube_query, integration_id="my_cube_integration", raw=True
        )

        # Verify the request includes raw parameter as query param
        mock_post.assert_called_once_with(
            "https://api.definite.app/v1/query?raw=true",
            json={
                "cube_query": cube_query,
                "integration_id": "my_cube_integration",
                "persist": True,
            },
            headers={"Authorization": "Bearer test_api_key"},
        )

        # Verify the result
        assert result["success"] is True
        assert result["raw_data"] == [{"value": 100}]

    @patch("definite_sdk.sql.requests.post")
    def test_execute_sql_http_error(self, mock_post):
        """Test handling of HTTP errors during SQL execution."""
        # Mock error response
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("API Error")
        mock_post.return_value = mock_response

        # Execute query and expect HTTPError
        with pytest.raises(requests.HTTPError):
            self.sql_client.execute("SELECT * FROM non_existent_table")

    @patch("definite_sdk.sql.requests.post")
    def test_execute_cube_query_http_error(self, mock_post):
        """Test handling of HTTP errors during Cube query execution."""
        # Mock error response
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("API Error")
        mock_post.return_value = mock_response

        # Prepare cube query
        cube_query = {"dimensions": [], "measures": ["invalid.measure"], "limit": 1000}

        # Execute query and expect HTTPError
        with pytest.raises(requests.HTTPError):
            self.sql_client.execute_cube_query(cube_query)


# Integration tests (require real API key)
@pytest.mark.integration
def test_real_api_integration():
    """Integration test with real API (requires DEF_API_KEY environment variable)."""
    api_key = os.environ.get("DEF_API_KEY")
    if not api_key:
        pytest.skip("DEF_API_KEY environment variable not set")

    client = DefiniteClient(api_key)
    sql_client = client.get_sql_client()

    # This test would require a real integration and valid SQL query
    # For now, just verify the client is created successfully
    assert isinstance(sql_client, DefiniteSqlClient)
    assert sql_client._api_key == api_key
