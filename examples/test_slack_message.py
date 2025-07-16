#!/usr/bin/env python
"""
Example script to test Slack messaging functionality
"""
import os
import sys
from definite_sdk import DefiniteClient

def main():
    # Get API key from environment
    api_key = os.getenv("DEF_API_KEY") or os.getenv("DEFINITE_API_KEY")
    if not api_key:
        print("Error: Please set DEF_API_KEY or DEFINITE_API_KEY environment variable")
        sys.exit(1)
    
    # Configuration - UPDATE THESE VALUES
    SLACK_INTEGRATION_ID = os.getenv("SLACK_INTEGRATION_ID", "your_slack_integration_id")
    CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID", "C0920MVPWFN")
    
    # Initialize client
    client = DefiniteClient(api_key)
    message_client = client.get_message_client()
    
    try:
        # Example 1: Simple text message using unified interface
        print("Sending simple text message...")
        result = message_client.send_message(
            channel="slack",
            integration_id=SLACK_INTEGRATION_ID,
            to=CHANNEL_ID,
            content="Hello from Definite SDK! 👋 This is a test message."
        )
        print(f"✅ Message sent successfully! Timestamp: {result.get('ts', 'N/A')}")
        
        # Example 2: Message with Slack blocks
        print("\nSending message with blocks...")
        result = message_client.send_message(
            channel="slack",
            integration_id=SLACK_INTEGRATION_ID,
            to=CHANNEL_ID,
            content="Fallback text",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Definite SDK Test*\nThis message includes _formatted_ text!"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": "*Status:*\n✅ Working"},
                        {"type": "mrkdwn", "text": "*Version:*\n0.1.8"}
                    ]
                }
            ]
        )
        print(f"✅ Block message sent! Timestamp: {result.get('ts', 'N/A')}")
        
        # Example 3: Using convenience method
        print("\nSending via convenience method...")
        result = message_client.send_slack_message(
            integration_id=SLACK_INTEGRATION_ID,
            channel_id=CHANNEL_ID,
            text="Testing the convenience method! 🚀"
        )
        print(f"✅ Convenience method worked! Timestamp: {result.get('ts', 'N/A')}")
        
        # Example 4: Reply to thread (if you have a thread_ts)
        if result.get('ts'):
            print("\nSending threaded reply...")
            thread_result = message_client.send_slack_message(
                integration_id=SLACK_INTEGRATION_ID,
                channel_id=CHANNEL_ID,
                text="This is a reply in the thread!",
                thread_ts=result['ts']
            )
            print(f"✅ Thread reply sent! Timestamp: {thread_result.get('ts', 'N/A')}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"Response details: {e.response.text}")

if __name__ == "__main__":
    main()