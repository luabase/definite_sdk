import os
import json
from unittest.mock import Mock, patch
import pytest

from definite_sdk import DefiniteClient


class TestDuckLakeIntegration:
    """Test DuckLake integration functionality."""

    @patch('requests.get')
    def test_attach_ducklake_default_alias(self, mock_get):
        """Test attach_ducklake with default alias."""
        # Mock the API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "name": "DuckLake",
            "pg_host": "db.example.supabase.co",
            "pg_port": 6543,
            "pg_user": "user_test_123",
            "pg_schema": "team_test_123",
            "pg_database": "postgres",
            "pg_password": "test_password",
            "gcs_bucket_path": "def-ducklake-staging/test-bucket",
            "gcs_access_key_id": "TEST_ACCESS_KEY",
            "gcs_secret_access_key": "test_secret_key",
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Test the method
        client = DefiniteClient("test_api_key")
        sql = client.attach_ducklake()

        # Verify API call
        mock_get.assert_called_once_with(
            "https://api.definite.app/v1/api/integration/DuckLake",
            headers={"Authorization": "Bearer test_api_key"}
        )

        # Verify SQL generation
        assert "CREATE SECRET (" in sql
        assert "TYPE gcs" in sql
        assert "KEY_ID 'TEST_ACCESS_KEY'" in sql
        assert "SECRET 'test_secret_key'" in sql
        assert "ATTACH 'ducklake:postgres:" in sql
        assert "AS lake" in sql  # default alias
        assert "DATA_PATH 'gs://def-ducklake-staging/test-bucket'" in sql
        assert "METADATA_SCHEMA 'team_test_123'" in sql
        assert "postgresql://user_test_123:test_password@db.example.supabase.co:6543/postgres" in sql

    @patch('requests.get')
    def test_attach_ducklake_custom_alias(self, mock_get):
        """Test attach_ducklake with custom alias."""
        # Mock the API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "name": "DuckLake",
            "pg_host": "db.example.supabase.co",
            "pg_port": 6543,
            "pg_user": "user_test_123",
            "pg_schema": "team_test_123",
            "pg_database": "postgres",
            "pg_password": "test_password",
            "gcs_bucket_path": "def-ducklake-staging/test-bucket",
            "gcs_access_key_id": "TEST_ACCESS_KEY",
            "gcs_secret_access_key": "test_secret_key",
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Test the method with custom alias
        client = DefiniteClient("test_api_key")
        sql = client.attach_ducklake(alias="warehouse")

        # Verify SQL generation with custom alias
        assert "AS warehouse" in sql
        assert "AS lake" not in sql

    @patch('requests.get')
    def test_attach_ducklake_api_error(self, mock_get):
        """Test attach_ducklake when API returns an error."""
        # Mock API error
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("API Error")
        mock_get.return_value = mock_response

        # Test that error is raised
        client = DefiniteClient("test_api_key")
        with pytest.raises(Exception, match="API Error"):
            client.attach_ducklake() 