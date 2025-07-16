import pytest
from unittest.mock import Mock, patch
from definite_sdk import DefiniteClient
from definite_sdk.message import DefiniteMessageClient


@pytest.fixture
def api_key():
    return "test_api_key"


@pytest.fixture
def message_client(api_key):
    return DefiniteMessageClient(api_key, "https://api.definite.app")


class TestDefiniteMessageClient:
    def test_init(self, api_key):
        client = DefiniteMessageClient(api_key, "https://api.definite.app")
        assert client._api_key == api_key
        assert client._message_url == "https://api.definite.app/v3"

    @patch("requests.post")
    def test_send_slack_message_simple(self, mock_post, message_client):
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True, "ts": "1234567890.123456"}
        mock_post.return_value = mock_response

        # Send message
        result = message_client.send_message(
            channel="slack",
            integration_id="slack_123",
            to="C0920MVPWFN",
            content="Hello from test!"
        )

        # Verify request
        mock_post.assert_called_once_with(
            "https://api.definite.app/v3/slack/message",
            json={
                "integration_id": "slack_123",
                "channel_id": "C0920MVPWFN",
                "text": "Hello from test!"
            },
            headers={"Authorization": "Bearer test_api_key"}
        )

        assert result == {"ok": True, "ts": "1234567890.123456"}

    @patch("requests.post")
    def test_send_slack_message_with_blocks(self, mock_post, message_client):
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True, "ts": "1234567890.123456"}
        mock_post.return_value = mock_response

        # Test blocks
        blocks = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*Bold text*"}
            }
        ]

        # Send message
        result = message_client.send_message(
            channel="slack",
            integration_id="slack_123",
            to="C0920MVPWFN",
            content="Fallback text",
            blocks=blocks
        )

        # Verify request
        mock_post.assert_called_once_with(
            "https://api.definite.app/v3/slack/message",
            json={
                "integration_id": "slack_123",
                "channel_id": "C0920MVPWFN",
                "text": "Fallback text",
                "blocks": blocks
            },
            headers={"Authorization": "Bearer test_api_key"}
        )

    @patch("requests.post")
    def test_send_slack_message_with_thread(self, mock_post, message_client):
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True, "ts": "1234567890.123456"}
        mock_post.return_value = mock_response

        # Send threaded message
        result = message_client.send_message(
            channel="slack",
            integration_id="slack_123",
            to="C0920MVPWFN",
            content="Reply in thread",
            thread_ts="1234567890.000000"
        )

        # Verify request
        mock_post.assert_called_once_with(
            "https://api.definite.app/v3/slack/message",
            json={
                "integration_id": "slack_123",
                "channel_id": "C0920MVPWFN",
                "text": "Reply in thread",
                "thread_ts": "1234567890.000000"
            },
            headers={"Authorization": "Bearer test_api_key"}
        )

    @patch("requests.post")
    def test_send_slack_message_convenience_method(self, mock_post, message_client):
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True, "ts": "1234567890.123456"}
        mock_post.return_value = mock_response

        # Use convenience method
        result = message_client.send_slack_message(
            integration_id="slack_123",
            channel_id="C0920MVPWFN",
            text="Hello from convenience method!"
        )

        # Verify request
        mock_post.assert_called_once_with(
            "https://api.definite.app/v3/slack/message",
            json={
                "integration_id": "slack_123",
                "channel_id": "C0920MVPWFN",
                "text": "Hello from convenience method!"
            },
            headers={"Authorization": "Bearer test_api_key"}
        )

        assert result == {"ok": True, "ts": "1234567890.123456"}

    def test_send_message_unsupported_channel(self, message_client):
        with pytest.raises(ValueError, match="Unsupported channel: email"):
            message_client.send_message(
                channel="email",
                integration_id="email_123",
                to="test@example.com",
                content="Hello"
            )

    @patch("requests.post")
    def test_send_message_with_additional_kwargs(self, mock_post, message_client):
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True, "ts": "1234567890.123456"}
        mock_post.return_value = mock_response

        # Send message with additional kwargs
        result = message_client.send_message(
            channel="slack",
            integration_id="slack_123",
            to="C0920MVPWFN",
            content="Hello",
            custom_field="custom_value",
            another_field=123
        )

        # Verify additional fields are included
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        json_data = call_args[1]["json"]
        assert json_data["custom_field"] == "custom_value"
        assert json_data["another_field"] == 123

    def test_client_integration(self, api_key):
        client = DefiniteClient(api_key)
        message_client = client.get_message_client()
        assert isinstance(message_client, DefiniteMessageClient)
        assert message_client._api_key == api_key

        # Test alias method
        message_client2 = client.message_client()
        assert isinstance(message_client2, DefiniteMessageClient)
        assert message_client2._api_key == api_key