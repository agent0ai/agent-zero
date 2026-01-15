"""
Google Pub/Sub Integration for Real-Time Gmail Notifications
Enables push notifications for new emails via Google Cloud Pub/Sub
"""

import os
import json
import base64
from typing import Dict, Optional, Callable, Any
from datetime import datetime
import hashlib
import hmac

try:
    from google.cloud import pubsub_v1
    from google.oauth2 import service_account
    from google.auth.credentials import AnonymousCredentials
    from google.auth.exceptions import DefaultCredentialsError
except ImportError:
    pubsub_v1 = None
    service_account = None
    AnonymousCredentials = None
    DefaultCredentialsError = None

from python.helpers.gmail_oauth2 import GmailOAuth2Handler


class GmailPushNotifications:
    """Manages Gmail push notifications via Google Pub/Sub"""
    
    def __init__(
        self,
        project_id: str = None,
        topic_name: str = "gmail-push-notifications",
        subscription_name: str = "gmail-push-sub",
        credentials_path: str = None
    ):
        """
        Initialize Pub/Sub integration
        
        Args:
            project_id: Google Cloud project ID
            topic_name: Pub/Sub topic name
            subscription_name: Pub/Sub subscription name
            credentials_path: Path to service account JSON credentials
        """
        if pubsub_v1 is None:
            raise ImportError(
                "Google Cloud Pub/Sub library not installed. "
                "Run: pip install google-cloud-pubsub"
            )
        
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT_ID")
        self.topic_name = topic_name
        self.subscription_name = subscription_name
        
        # Initialize Pub/Sub clients
        credentials = None
        if credentials_path:
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path
            )
        
        try:
            self.publisher = pubsub_v1.PublisherClient(credentials=credentials)
            self.subscriber = pubsub_v1.SubscriberClient(credentials=credentials)
        except DefaultCredentialsError:
            if AnonymousCredentials is None:
                raise
            credentials = AnonymousCredentials()
            self.publisher = pubsub_v1.PublisherClient(credentials=credentials)
            self.subscriber = pubsub_v1.SubscriberClient(credentials=credentials)
        
        self.topic_path = self.publisher.topic_path(self.project_id, self.topic_name)
        self.subscription_path = self.subscriber.subscription_path(
            self.project_id, self.subscription_name
        )
        
        self.oauth_handler = GmailOAuth2Handler()
        self.message_handlers = []
    
    def setup_topic_and_subscription(self) -> Dict:
        """
        Create Pub/Sub topic and subscription if they don't exist
        
        Returns:
            Dict with setup status
        """
        try:
            # Create topic
            try:
                self.publisher.create_topic(request={"name": self.topic_path})
                topic_created = True
            except Exception:
                # Topic already exists
                topic_created = False
            
            # Create subscription
            try:
                self.subscriber.create_subscription(
                    request={
                        "name": self.subscription_path,
                        "topic": self.topic_path,
                        "ack_deadline_seconds": 60
                    }
                )
                subscription_created = True
            except Exception:
                # Subscription already exists
                subscription_created = False
            
            return {
                "success": True,
                "topic_path": self.topic_path,
                "subscription_path": self.subscription_path,
                "topic_created": topic_created,
                "subscription_created": subscription_created
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to setup Pub/Sub: {str(e)}"
            }
    
    def enable_push_notifications(self, account_name: str = "default") -> Dict:
        """
        Enable Gmail push notifications for an account
        
        Args:
            account_name: Name of the authenticated Gmail account
            
        Returns:
            Dict with watch status
        """
        try:
            service = self.oauth_handler.get_gmail_service(account_name)
            
            # Watch Gmail mailbox
            request = {
                'labelIds': ['INBOX'],
                'topicName': self.topic_path
            }
            
            watch_response = service.users().watch(
                userId='me',
                body=request
            ).execute()
            
            return {
                "success": True,
                "account_name": account_name,
                "history_id": watch_response.get('historyId'),
                "expiration": watch_response.get('expiration'),
                "topic": self.topic_path
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to enable push notifications: {str(e)}"
            }
    
    def disable_push_notifications(self, account_name: str = "default") -> Dict:
        """
        Disable Gmail push notifications for an account
        
        Args:
            account_name: Name of the authenticated Gmail account
            
        Returns:
            Dict with stop status
        """
        try:
            service = self.oauth_handler.get_gmail_service(account_name)
            
            service.users().stop(userId='me').execute()
            
            return {
                "success": True,
                "account_name": account_name,
                "message": "Push notifications stopped"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to stop push notifications: {str(e)}"
            }
    
    def register_message_handler(self, handler: Callable[[Dict], None]):
        """
        Register callback function for new messages
        
        Args:
            handler: Function that receives message data dict
        """
        self.message_handlers.append(handler)
    
    def _process_push_message(self, message: Any) -> Dict:
        """
        Process incoming Pub/Sub message
        
        Args:
            message: Pub/Sub message object
            
        Returns:
            Dict with processed notification data
        """
        try:
            # Decode message data
            data = json.loads(message.data.decode('utf-8'))
            
            notification = {
                "email_address": data.get('emailAddress'),
                "history_id": data.get('historyId'),
                "timestamp": datetime.now().isoformat(),
                "message_id": message.message_id
            }
            
            # Acknowledge message
            message.ack()
            
            # Call registered handlers
            for handler in self.message_handlers:
                try:
                    handler(notification)
                except Exception as e:
                    print(f"Error in message handler: {e}")
            
            return notification
            
        except Exception as e:
            # Nack message on error
            message.nack()
            return {
                "error": f"Failed to process message: {str(e)}"
            }
    
    def start_listening(self, callback: Callable[[Dict], None] = None):
        """
        Start listening for push notifications
        
        Args:
            callback: Optional callback function for each notification
        """
        if callback:
            self.register_message_handler(callback)
        
        # Start async subscription
        streaming_pull_future = self.subscriber.subscribe(
            self.subscription_path,
            callback=self._process_push_message
        )
        
        print(f"Listening for push notifications on {self.subscription_path}")
        
        try:
            # Block until interrupted
            streaming_pull_future.result()
        except KeyboardInterrupt:
            streaming_pull_future.cancel()
            print("Stopped listening for notifications")
    
    def get_notification_history(
        self,
        account_name: str,
        start_history_id: str,
        max_results: int = 100
    ) -> Dict:
        """
        Get Gmail history since last notification
        
        Args:
            account_name: Name of the authenticated Gmail account
            start_history_id: Starting history ID from notification
            max_results: Maximum number of history records
            
        Returns:
            Dict with history data
        """
        try:
            service = self.oauth_handler.get_gmail_service(account_name)
            
            history = service.users().history().list(
                userId='me',
                startHistoryId=start_history_id,
                maxResults=max_results
            ).execute()
            
            changes = []
            
            for record in history.get('history', []):
                # Process messages added
                for msg in record.get('messagesAdded', []):
                    changes.append({
                        "type": "message_added",
                        "message_id": msg['message']['id'],
                        "labels": msg['message'].get('labelIds', [])
                    })
                
                # Process labels added
                for label in record.get('labelsAdded', []):
                    changes.append({
                        "type": "label_added",
                        "message_id": label['message']['id'],
                        "labels": label.get('labelIds', [])
                    })
                
                # Process labels removed
                for label in record.get('labelsRemoved', []):
                    changes.append({
                        "type": "label_removed",
                        "message_id": label['message']['id'],
                        "labels": label.get('labelIds', [])
                    })
            
            return {
                "success": True,
                "history_id": history.get('historyId'),
                "changes": changes,
                "next_page_token": history.get('nextPageToken')
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get history: {str(e)}"
            }


class WebhookHandler:
    """Handles Gmail webhook notifications from Pub/Sub"""
    
    def __init__(self, secret_token: str = None):
        """
        Initialize webhook handler
        
        Args:
            secret_token: Secret token for webhook verification
        """
        self.secret_token = secret_token or os.getenv("GMAIL_WEBHOOK_SECRET")
        self.notification_callbacks = []
    
    def verify_webhook(self, data: bytes, signature: str) -> bool:
        """
        Verify webhook signature
        
        Args:
            data: Raw webhook data
            signature: HMAC signature from headers
            
        Returns:
            True if signature is valid
        """
        if not self.secret_token:
            # No verification if no secret configured
            return True
        
        expected_signature = hmac.new(
            self.secret_token.encode(),
            data,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    def process_webhook(self, request_data: Dict) -> Dict:
        """
        Process webhook POST data
        
        Args:
            request_data: Webhook request data
            
        Returns:
            Dict with processing result
        """
        try:
            # Extract Pub/Sub message
            message = request_data.get('message', {})
            
            # Decode data
            if 'data' in message:
                decoded_data = base64.b64decode(message['data']).decode('utf-8')
                notification = json.loads(decoded_data)
            else:
                notification = {}
            
            result = {
                "success": True,
                "notification": notification,
                "timestamp": datetime.now().isoformat()
            }
            
            # Call registered callbacks
            for callback in self.notification_callbacks:
                try:
                    callback(notification)
                except Exception as e:
                    print(f"Error in webhook callback: {e}")
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to process webhook: {str(e)}"
            }
    
    def register_callback(self, callback: Callable[[Dict], None]):
        """
        Register callback for webhook notifications
        
        Args:
            callback: Function to call with notification data
        """
        self.notification_callbacks.append(callback)
