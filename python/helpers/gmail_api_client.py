"""
Gmail API Client Wrapper
Advanced Gmail operations using Google Gmail API
"""

import base64
import mimetypes
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime, timedelta

try:
    from googleapiclient.errors import HttpError
except ImportError:
    HttpError = Exception

from python.helpers.gmail_oauth2 import GmailOAuth2Handler


class GmailAPIClient:
    """Advanced Gmail operations using Gmail API"""
    
    def __init__(self, account_name: str = "default"):
        """
        Initialize Gmail API client
        
        Args:
            account_name: Name of the authenticated account to use
        """
        self.account_name = account_name
        self.oauth_handler = GmailOAuth2Handler()
        self.service = None
        self._ensure_service()
    
    def _ensure_service(self):
        """Ensure Gmail service is available"""
        if not self.service:
            try:
                self.service = self.oauth_handler.get_gmail_service(self.account_name)
            except Exception as e:
                raise ValueError(f"Failed to get Gmail service for {self.account_name}: {e}")
    
    # Email Sending with Advanced Features
    
    def send_email(
        self,
        to: List[str],
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
        html: bool = False,
        from_name: Optional[str] = None,
        labels: Optional[List[str]] = None,
        thread_id: Optional[str] = None
    ) -> Dict:
        """
        Send email via Gmail API
        
        Args:
            to: List of recipient email addresses
            subject: Email subject
            body: Email body (plain text or HTML)
            cc: CC recipients
            bcc: BCC recipients
            attachments: List of file paths to attach
            html: Whether body is HTML
            from_name: Display name for sender
            labels: Gmail labels to apply to sent message
            thread_id: Thread ID to reply to
            
        Returns:
            Dict with send result
        """
        try:
            self._ensure_service()
            
            # Create message
            message = self._create_message(
                to=to,
                subject=subject,
                body=body,
                cc=cc,
                bcc=bcc,
                attachments=attachments,
                html=html,
                from_name=from_name
            )
            
            # Add metadata
            send_data = {'raw': message}
            if thread_id:
                send_data['threadId'] = thread_id
            if labels:
                send_data['labelIds'] = labels
            
            # Send message
            sent_message = self.service.users().messages().send(
                userId='me',
                body=send_data
            ).execute()
            
            return {
                "success": True,
                "message_id": sent_message['id'],
                "thread_id": sent_message.get('threadId'),
                "to": to,
                "subject": subject,
                "labels": labels
            }
            
        except HttpError as error:
            return {
                "success": False,
                "error": f"Gmail API error: {error}",
                "error_code": error.resp.status if hasattr(error, 'resp') else None
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _create_message(
        self,
        to: List[str],
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
        html: bool = False,
        from_name: Optional[str] = None
    ) -> str:
        """Create base64 encoded email message"""
        
        # Create message container
        if attachments:
            message = MIMEMultipart()
        else:
            message = MIMEText(body, 'html' if html else 'plain')
            message['subject'] = subject
            message['to'] = ', '.join(to)
            if cc:
                message['cc'] = ', '.join(cc)
            if from_name:
                message['from'] = from_name
            return base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        # Add headers
        message['subject'] = subject
        message['to'] = ', '.join(to)
        if cc:
            message['cc'] = ', '.join(cc)
        if bcc:
            message['bcc'] = ', '.join(bcc)
        if from_name:
            message['from'] = from_name
        
        # Add body
        message.attach(MIMEText(body, 'html' if html else 'plain'))
        
        # Add attachments
        for file_path in (attachments or []):
            self._add_attachment(message, file_path)
        
        return base64.urlsafe_b64encode(message.as_bytes()).decode()
    
    def _add_attachment(self, message: MIMEMultipart, file_path: str):
        """Add attachment to message"""
        path = Path(file_path)
        
        if not path.exists():
            return
        
        content_type, _ = mimetypes.guess_type(file_path)
        
        if content_type is None:
            content_type = 'application/octet-stream'
        
        main_type, sub_type = content_type.split('/', 1)
        
        with open(file_path, 'rb') as f:
            attachment = MIMEBase(main_type, sub_type)
            attachment.set_payload(f.read())
        
        encoders.encode_base64(attachment)
        attachment.add_header('Content-Disposition', 'attachment', filename=path.name)
        message.attach(attachment)
    
    # Advanced Email Reading
    
    def read_emails(
        self,
        query: str = None,
        max_results: int = 10,
        label_ids: Optional[List[str]] = None,
        include_spam_trash: bool = False
    ) -> List[Dict]:
        """
        Read emails with advanced filtering
        
        Args:
            query: Gmail search query (e.g., "is:unread from:example.com")
            max_results: Maximum number of emails to return
            label_ids: Filter by label IDs
            include_spam_trash: Include spam and trash folders
            
        Returns:
            List of email dicts
        """
        try:
            self._ensure_service()
            
            # Build query parameters
            params = {
                'userId': 'me',
                'maxResults': max_results
            }
            
            if query:
                params['q'] = query
            
            if label_ids:
                params['labelIds'] = label_ids
            
            if include_spam_trash:
                params['includeSpamTrash'] = True
            
            # Get message list
            results = self.service.users().messages().list(**params).execute()
            messages = results.get('messages', [])
            
            # Fetch full message details
            emails = []
            for msg in messages:
                email_data = self._get_message_details(msg['id'])
                if email_data:
                    emails.append(email_data)
            
            return emails
            
        except HttpError as error:
            print(f"Gmail API error: {error}")
            return []
        except Exception as e:
            print(f"Error reading emails: {e}")
            return []
    
    def _get_message_details(self, message_id: str) -> Optional[Dict]:
        """Get full message details"""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            # Extract headers
            headers = {h['name']: h['value'] for h in message['payload'].get('headers', [])}
            
            # Extract body
            body = self._extract_body(message['payload'])
            
            # Extract labels
            labels = message.get('labelIds', [])
            
            return {
                "message_id": message_id,
                "thread_id": message.get('threadId'),
                "from": headers.get('From'),
                "to": headers.get('To'),
                "subject": headers.get('Subject'),
                "date": headers.get('Date'),
                "body": body,
                "labels": labels,
                "snippet": message.get('snippet'),
                "is_unread": 'UNREAD' in labels
            }
            
        except Exception as e:
            print(f"Error getting message {message_id}: {e}")
            return None
    
    def _extract_body(self, payload: Dict) -> str:
        """Extract email body from payload"""
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data')
                    if data:
                        return base64.urlsafe_b64decode(data).decode('utf-8')
                elif part['mimeType'] == 'multipart/alternative':
                    return self._extract_body(part)
        
        if 'body' in payload and 'data' in payload['body']:
            return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
        
        return ""
    
    # Label Management
    
    def create_label(self, name: str, label_list_visibility: str = "labelShow",
                    message_list_visibility: str = "show") -> Dict:
        """
        Create a new Gmail label
        
        Args:
            name: Label name
            label_list_visibility: "labelShow", "labelShowIfUnread", "labelHide"
            message_list_visibility: "show" or "hide"
            
        Returns:
            Dict with label info
        """
        try:
            self._ensure_service()
            
            label_object = {
                'name': name,
                'labelListVisibility': label_list_visibility,
                'messageListVisibility': message_list_visibility
            }
            
            label = self.service.users().labels().create(
                userId='me',
                body=label_object
            ).execute()
            
            return {
                "success": True,
                "label_id": label['id'],
                "label_name": label['name']
            }
            
        except HttpError as error:
            return {
                "success": False,
                "error": f"Failed to create label: {error}"
            }
    
    def list_labels(self) -> List[Dict]:
        """List all Gmail labels"""
        try:
            self._ensure_service()
            
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            
            return [
                {
                    "label_id": label['id'],
                    "label_name": label['name'],
                    "type": label.get('type', 'user')
                }
                for label in labels
            ]
            
        except HttpError as error:
            print(f"Error listing labels: {error}")
            return []
    
    def apply_labels(self, message_ids: List[str], label_ids: List[str]) -> Dict:
        """Apply labels to messages"""
        try:
            self._ensure_service()
            
            self.service.users().messages().batchModify(
                userId='me',
                body={
                    'ids': message_ids,
                    'addLabelIds': label_ids
                }
            ).execute()
            
            return {
                "success": True,
                "messages_modified": len(message_ids),
                "labels_applied": label_ids
            }
            
        except HttpError as error:
            return {
                "success": False,
                "error": f"Failed to apply labels: {error}"
            }
    
    def remove_labels(self, message_ids: List[str], label_ids: List[str]) -> Dict:
        """Remove labels from messages"""
        try:
            self._ensure_service()
            
            self.service.users().messages().batchModify(
                userId='me',
                body={
                    'ids': message_ids,
                    'removeLabelIds': label_ids
                }
            ).execute()
            
            return {
                "success": True,
                "messages_modified": len(message_ids),
                "labels_removed": label_ids
            }
            
        except HttpError as error:
            return {
                "success": False,
                "error": f"Failed to remove labels: {error}"
            }
    
    # Draft Management
    
    def create_draft(
        self,
        to: List[str],
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
        html: bool = False
    ) -> Dict:
        """Create email draft"""
        try:
            self._ensure_service()
            
            message = self._create_message(
                to=to,
                subject=subject,
                body=body,
                cc=cc,
                bcc=bcc,
                attachments=attachments,
                html=html
            )
            
            draft = self.service.users().drafts().create(
                userId='me',
                body={'message': {'raw': message}}
            ).execute()
            
            return {
                "success": True,
                "draft_id": draft['id'],
                "message_id": draft['message']['id']
            }
            
        except HttpError as error:
            return {
                "success": False,
                "error": f"Failed to create draft: {error}"
            }
    
    def list_drafts(self, max_results: int = 10) -> List[Dict]:
        """List email drafts"""
        try:
            self._ensure_service()
            
            results = self.service.users().drafts().list(
                userId='me',
                maxResults=max_results
            ).execute()
            
            drafts = results.get('drafts', [])
            
            return [
                {
                    "draft_id": draft['id'],
                    "message_id": draft['message']['id']
                }
                for draft in drafts
            ]
            
        except HttpError as error:
            print(f"Error listing drafts: {error}")
            return []
    
    def send_draft(self, draft_id: str) -> Dict:
        """Send existing draft"""
        try:
            self._ensure_service()
            
            sent = self.service.users().drafts().send(
                userId='me',
                body={'id': draft_id}
            ).execute()
            
            return {
                "success": True,
                "message_id": sent['id'],
                "thread_id": sent.get('threadId')
            }
            
        except HttpError as error:
            return {
                "success": False,
                "error": f"Failed to send draft: {error}"
            }
    
    def delete_draft(self, draft_id: str) -> Dict:
        """Delete draft"""
        try:
            self._ensure_service()
            
            self.service.users().drafts().delete(
                userId='me',
                id=draft_id
            ).execute()
            
            return {
                "success": True,
                "draft_id": draft_id
            }
            
        except HttpError as error:
            return {
                "success": False,
                "error": f"Failed to delete draft: {error}"
            }
    
    # Advanced Search
    
    def search_emails(
        self,
        sender: Optional[str] = None,
        recipient: Optional[str] = None,
        subject: Optional[str] = None,
        keywords: Optional[str] = None,
        has_attachment: bool = None,
        is_unread: bool = None,
        after_date: Optional[str] = None,
        before_date: Optional[str] = None,
        max_results: int = 10
    ) -> List[Dict]:
        """
        Advanced email search with multiple criteria
        
        Args:
            sender: Filter by sender email
            recipient: Filter by recipient email  
            subject: Filter by subject keywords
            keywords: Search keywords in email body
            has_attachment: Filter emails with attachments
            is_unread: Filter unread emails
            after_date: Emails after date (YYYY/MM/DD)
            before_date: Emails before date (YYYY/MM/DD)
            max_results: Maximum results to return
            
        Returns:
            List of matching emails
        """
        # Build Gmail query
        query_parts = []
        
        if sender:
            query_parts.append(f"from:{sender}")
        if recipient:
            query_parts.append(f"to:{recipient}")
        if subject:
            query_parts.append(f"subject:{subject}")
        if keywords:
            query_parts.append(keywords)
        if has_attachment is not None:
            query_parts.append("has:attachment" if has_attachment else "-has:attachment")
        if is_unread is not None:
            query_parts.append("is:unread" if is_unread else "-is:unread")
        if after_date:
            query_parts.append(f"after:{after_date}")
        if before_date:
            query_parts.append(f"before:{before_date}")
        
        query = ' '.join(query_parts) if query_parts else None
        
        return self.read_emails(query=query, max_results=max_results)
