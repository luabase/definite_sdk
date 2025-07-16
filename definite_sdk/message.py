from typing import Any, Dict, List, Optional

import requests

MESSAGE_ENDPOINT = "/v3"


class DefiniteMessageClient:
    """
    A message client for sending messages via various channels through the Definite API.

    Initialization:
    >>> client = DefiniteClient("MY_API_KEY")
    >>> message_client = client.get_message_client()

    Sending messages:
    >>> # Send a Slack message
    >>> result = message_client.send_message(
    ...     channel="slack",
    ...     integration_id="slack_integration_id",
    ...     to="C0920MVPWFN",  # channel_id
    ...     content="Hello from Definite SDK!"
    ... )
    
    >>> # Send a Slack message with blocks and thread
    >>> result = message_client.send_message(
    ...     channel="slack",
    ...     integration_id="slack_integration_id",
    ...     to="C0920MVPWFN",
    ...     content="Hello!",
    ...     blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": "Hello!"}}],
    ...     thread_ts="1234567890.123456"
    ... )
    """

    def __init__(self, api_key: str, api_url: str):
        """
        Initializes the DefiniteMessageClient.

        Args:
            api_key (str): The API key for authorization.
            api_url (str): The base URL for the Definite API.
        """
        self._api_key = api_key
        self._message_url = api_url + MESSAGE_ENDPOINT

    def send_message(
        self,
        channel: str,
        integration_id: str,
        to: str,
        content: str,
        subject: Optional[str] = None,
        blocks: Optional[List[Dict[str, Any]]] = None,
        thread_ts: Optional[str] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Sends a message through the specified channel.

        Args:
            channel (str): The messaging channel to use (e.g., "slack", "email").
            integration_id (str): The ID of the integration to use.
            to (str): The recipient identifier (channel_id for Slack, email address for email).
            content (str): The message content (text for Slack, body for email).
            subject (Optional[str]): Subject line (used for email).
            blocks (Optional[List[Dict[str, Any]]]): Slack Block Kit blocks for formatting.
            thread_ts (Optional[str]): Slack thread timestamp to reply to.
            **kwargs: Additional channel-specific parameters.

        Returns:
            Dict[str, Any]: The response from the API.

        Raises:
            requests.HTTPError: If the API request fails.
            ValueError: If the channel is not supported.

        Example:
            >>> # Slack message
            >>> result = message_client.send_message(
            ...     channel="slack",
            ...     integration_id="slack_123",
            ...     to="C0920MVPWFN",
            ...     content="Hello team!"
            ... )
            
            >>> # Slack message with blocks
            >>> result = message_client.send_message(
            ...     channel="slack",
            ...     integration_id="slack_123",
            ...     to="C0920MVPWFN",
            ...     content="Fallback text",
            ...     blocks=[{
            ...         "type": "section",
            ...         "text": {"type": "mrkdwn", "text": "*Important Update*"}
            ...     }]
            ... )
        """
        channel_lower = channel.lower()
        
        if channel_lower == "slack":
            return self._send_slack_message(
                integration_id=integration_id,
                channel_id=to,
                text=content,
                blocks=blocks,
                thread_ts=thread_ts,
                **kwargs
            )
        else:
            raise ValueError(f"Unsupported channel: {channel}")

    def _send_slack_message(
        self,
        integration_id: str,
        channel_id: str,
        text: str,
        blocks: Optional[List[Dict[str, Any]]] = None,
        thread_ts: Optional[str] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Internal method to send a Slack message.

        Args:
            integration_id (str): The Slack integration ID.
            channel_id (str): The Slack channel ID.
            text (str): The message text.
            blocks (Optional[List[Dict[str, Any]]]): Slack blocks for formatting.
            thread_ts (Optional[str]): Thread timestamp for replies.
            **kwargs: Additional Slack-specific parameters.

        Returns:
            Dict[str, Any]: The API response.
        """
        url = f"{self._message_url}/slack/message"
        
        payload = {
            "integration_id": integration_id,
            "channel_id": channel_id,
            "text": text
        }
        
        if blocks:
            payload["blocks"] = blocks
        if thread_ts:
            payload["thread_ts"] = thread_ts
            
        # Add any additional kwargs to the payload
        payload.update(kwargs)

        response = requests.post(
            url,
            json=payload,
            headers={"Authorization": "Bearer " + self._api_key},
        )
        response.raise_for_status()
        return response.json()

    def send_slack_message(
        self,
        integration_id: str,
        channel_id: str,
        text: str,
        blocks: Optional[List[Dict[str, Any]]] = None,
        thread_ts: Optional[str] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Convenience method to send a Slack message directly.

        Args:
            integration_id (str): The Slack integration ID.
            channel_id (str): The Slack channel ID.
            text (str): The message text.
            blocks (Optional[List[Dict[str, Any]]]): Slack blocks for formatting.
            thread_ts (Optional[str]): Thread timestamp for replies.
            **kwargs: Additional Slack-specific parameters.

        Returns:
            Dict[str, Any]: The API response.

        Example:
            >>> result = message_client.send_slack_message(
            ...     integration_id="slack_123",
            ...     channel_id="C0920MVPWFN",
            ...     text="Hello from Definite SDK! 👋"
            ... )
            >>> print(f"Message sent! Timestamp: {result['ts']}")
        """
        return self.send_message(
            channel="slack",
            integration_id=integration_id,
            to=channel_id,
            content=text,
            blocks=blocks,
            thread_ts=thread_ts,
            **kwargs
        )