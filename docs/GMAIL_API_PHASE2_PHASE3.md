# Gmail Integration - Phase 2 & 3 Implementation Guide

## 🎯 Overview

**Phase 2:** Gmail API with OAuth2 - Multi-account support and advanced features
**Phase 3:** Real-time Push Notifications via Google Pub/Sub

**Status:** ✅ Complete
**Implementation Date:** January 14, 2026

---

## 📦 Phase 2: Gmail API with OAuth2

### Features Delivered

✅ **Multi-Account Management**

- Support multiple Gmail accounts with separate OAuth2 credentials
- Account names: sales@, support@, dev@, etc.
- Independent authentication and token management

✅ **Advanced Email Operations**

- Send via Gmail API with threading support
- Read with advanced filtering
- Search with Gmail query syntax
- Reply to existing threads

✅ **Label Management**

- Create custom labels
- Apply/remove labels from messages
- List all labels (system + user)
- Batch label operations

✅ **Draft Management**

- Create email drafts
- List existing drafts
- Send drafts
- Delete drafts

✅ **Advanced Search**

- Filter by sender, recipient, subject
- Search by keywords
- Filter by has_attachment
- Date range filtering
- Unread/read status

---

## 📦 Phase 3: Real-Time Push Notifications

### Features Delivered

✅ **Google Pub/Sub Integration**

- Create Pub/Sub topics and subscriptions
- Enable Gmail watch on mailboxes
- Receive real-time notifications for new emails

✅ **Push Notification Handling**

- Process incoming Pub/Sub messages
- Get Gmail history since last notification
- Track message additions, label changes
- Webhook endpoint support

✅ **Event Callbacks**

- Register custom handlers for new messages
- Process notifications asynchronously
- HMAC signature verification for webhooks

---

## 🔧 Setup Guide

### Prerequisites

1. **Google Cloud Console Setup**
   - Create new project at [console.cloud.google.com](https://console.cloud.google.com)
   - Enable Gmail API
   - Enable Cloud Pub/Sub API (for Phase 3)

2. **OAuth2 Credentials (Phase 2)**
   - Go to "APIs & Services" → "Credentials"
   - Create "OAuth 2.0 Client ID"
   - Application type: "Desktop app"
   - Download `credentials.json`
   - Save to `data/gmail_credentials/credentials.json`

3. **Service Account (Phase 3)**
   - Create service account for Pub/Sub
   - Grant "Pub/Sub Editor" role
   - Download JSON key file
   - Save to `data/gmail_credentials/service_account.json`

### Installation

```bash
# Install Phase 2 dependencies
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client

# Install Phase 3 dependencies
pip install google-cloud-pubsub
```

### Environment Variables

```bash
# Google Cloud Project (for Phase 3)
GOOGLE_CLOUD_PROJECT_ID="your-project-id"

# Optional webhook secret
GMAIL_WEBHOOK_SECRET="your-secret-token"
```

---

## 📚 Usage Examples

### Phase 2: OAuth2 & Gmail API

#### 1. Authenticate Account

```json
{
  "tool": "email_advanced",
  "action": "authenticate",
  "account_name": "sales",
  "credentials_json_path": "data/gmail_credentials/credentials.json"
}
```

**First Run:**

- Opens browser for Google OAuth consent
- User grants permissions
- Token saved to `data/gmail_credentials/token_sales.pickle`

**Subsequent Runs:**

- Uses saved token automatically
- Refreshes if expired

#### 2. Send Email via Gmail API

```json
{
  "tool": "email_advanced",
  "action": "send_gmail",
  "account_name": "sales",
  "to": ["customer@example.com"],
  "subject": "Your Custom Proposal",
  "body": "Dear Customer...",
  "attachments": ["tmp/proposal.pdf"],
  "labels": ["SENT", "Label_123"],
  "html": false
}
```

**Advantages over SMTP:**

- Higher rate limits (2,000/day with Workspace)
- Automatic threading
- Label support
- Access to sent messages

#### 3. Advanced Search

```json
{
  "tool": "email_advanced",
  "action": "search_advanced",
  "account_name": "support",
  "sender": "client@company.com",
  "has_attachment": true,
  "is_unread": true,
  "after_date": "2026/01/01",
  "keywords": "urgent"
}
```

**Search Operators:**

- `sender`: Filter by from address
- `recipient`: Filter by to address
- `subject`: Subject keywords
- `keywords`: Body search
- `has_attachment`: true/false
- `is_unread`: true/false
- `after_date`: YYYY/MM/DD format
- `before_date`: YYYY/MM/DD format

#### 4. Create and Apply Labels

```json
// Create label
{
  "tool": "email_advanced",
  "action": "create_label",
  "account_name": "sales",
  "label_name": "Customers/High Priority"
}

// Apply to messages
{
  "tool": "email_advanced",
  "action": "apply_labels",
  "account_name": "sales",
  "message_ids": ["msg_123", "msg_456"],
  "label_ids": ["Label_789"]
}
```

**Label Hierarchy:**

- Use `/` for nested labels
- Example: `Customers/High Priority`
- Creates parent-child relationship

#### 5. Draft Workflow

```json
// Create draft
{
  "tool": "email_advanced",
  "action": "create_draft",
  "account_name": "sales",
  "to": ["prospect@company.com"],
  "subject": "Follow-up",
  "body": "Thank you for your interest..."
}

// List drafts
{
  "tool": "email_advanced",
  "action": "list_drafts",
  "account_name": "sales",
  "max_results": 10
}

// Send draft
{
  "tool": "email_advanced",
  "action": "send_draft",
  "account_name": "sales",
  "draft_id": "draft_123"
}
```

#### 6. Multi-Account Management

```json
// List all authenticated accounts
{
  "tool": "email_advanced",
  "action": "list_accounts"
}

// Output:
// Account: sales | Email: sales@company.com | ✅ Authenticated
// Account: support | Email: support@company.com | ✅ Authenticated
// Account: dev | Email: dev@company.com | ✅ Authenticated
```

**Use Cases:**

- `sales@` - Customer proposals and follow-ups
- `support@` - Customer service emails
- `dev@` - Technical communications
- `manager@` - Internal reports and digests

### Phase 3: Push Notifications

#### 1. Enable Push Notifications

```json
{
  "tool": "email_advanced",
  "action": "enable_push",
  "account_name": "support",
  "project_id": "your-gcp-project-id"
}
```

**What Happens:**

- Creates Pub/Sub topic if not exists
- Creates subscription if not exists
- Registers Gmail watch on mailbox
- Returns history ID and expiration

**Watch Duration:**

- Typically 7 days
- Must renew before expiration
- Agent Jumbo can auto-renew

#### 2. Disable Push Notifications

```json
{
  "tool": "email_advanced",
  "action": "disable_push",
  "account_name": "support"
}
```

#### 3. Handle Push Notifications (Python)

```python
from python.helpers.gmail_push_notifications import GmailPushNotifications

def handle_new_email(notification):
    """Callback for new email notifications"""
    print(f"New email! History ID: {notification['history_id']}")

    # Get changes since last notification
    push = GmailPushNotifications(project_id="your-project")
    history = push.get_notification_history(
        account_name="support",
        start_history_id=notification['history_id']
    )

    for change in history.get('changes', []):
        if change['type'] == 'message_added':
            # Process new message
            message_id = change['message_id']
            # Read message, trigger workflow, etc.

# Register handler
push = GmailPushNotifications(project_id="your-project")
push.register_message_handler(handle_new_email)

# Start listening
push.start_listening()
```

#### 4. Webhook Integration

```python
from python.helpers.gmail_push_notifications import WebhookHandler
from flask import Flask, request

app = Flask(__name__)
webhook = WebhookHandler(secret_token="your-secret")

@app.route('/gmail/webhook', methods=['POST'])
def gmail_webhook():
    # Verify signature
    signature = request.headers.get('X-Goog-Signature')
    if not webhook.verify_webhook(request.data, signature):
        return 'Invalid signature', 401

    # Process notification
    result = webhook.process_webhook(request.get_json())

    return 'OK', 200

# Register callback
def on_notification(data):
    # Process new email
    print(f"Webhook received: {data}")

webhook.register_callback(on_notification)

app.run(port=5000)
```

---

## 🔐 Security Considerations

### OAuth2 Tokens

**Storage:**

- Tokens stored in `data/gmail_credentials/token_*.pickle`
- Encrypted with system credentials
- Never commit to Git

**Refresh:**

- Automatic token refresh when expired
- Refresh tokens valid for 6 months (default)
- Re-authentication required after expiration

**Scopes:**

```python
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',  # Read emails
    'https://www.googleapis.com/auth/gmail.send',      # Send emails
    'https://www.googleapis.com/auth/gmail.modify',    # Modify labels
    'https://www.googleapis.com/auth/gmail.labels',    # Manage labels
    'https://www.googleapis.com/auth/gmail.compose'    # Create drafts
]
```

### Pub/Sub Security

**Service Account:**

- Least privilege principle
- Only "Pub/Sub Editor" role needed
- Separate from OAuth2 credentials

**Webhook Verification:**

- HMAC-SHA256 signature verification
- Secret token in environment variable
- Prevents unauthorized requests

---

## 📊 Rate Limits & Quotas

### Gmail API Quotas

| Operation | Personal Gmail | Google Workspace |
|-----------|---------------|------------------|
| **Send** | 100/day | 2,000/day |
| **Read** | 1,000,000,000/day | Unlimited |
| **Modify** | 1,000/day | 100,000/day |
| **Labels** | 250 queries/user/second | 250 queries/user/second |

### Pub/Sub Quotas

| Resource | Quota |
|----------|-------|
| **Publish requests** | 10,000/second |
| **Subscriptions** | 10,000/project |
| **Messages** | Unlimited |

---

## 🎯 Use Cases

### Use Case 1: Multi-Department Email Management

```python
# Sales team
await email_advanced.execute(
    action="send_gmail",
    account_name="sales",
    to=["prospect@company.com"],
    subject="Proposal",
    labels=["Proposals", "High Priority"]
)

# Support team
await email_advanced.execute(
    action="read_gmail",
    account_name="support",
    query="is:unread label:urgent"
)

# Development team
await email_advanced.execute(
    action="search_advanced",
    account_name="dev",
    keywords="bug report",
    has_attachment=true
)
```

### Use Case 2: Customer Lifecycle with Labels

```python
# Lead captured
customer_id = lifecycle.capture_lead(...)

# Send welcome email with label
await email_advanced.execute(
    action="send_gmail",
    account_name="sales",
    to=[customer_email],
    subject="Welcome!",
    labels=["Customers/New Leads", f"Customer_{customer_id}"]
)

# Proposal sent with tracking label
await email_advanced.execute(
    action="send_gmail",
    to=[customer_email],
    subject="Proposal",
    labels=["Proposals/Sent", f"Customer_{customer_id}"]
)

# Search all emails for customer
emails = await email_advanced.execute(
    action="search_advanced",
    keywords=f"Customer_{customer_id}"
)
```

### Use Case 3: Real-Time Customer Response Handling

```python
# Enable push notifications for support inbox
await email_advanced.execute(
    action="enable_push",
    account_name="support"
)

# Handler processes new support tickets instantly
def handle_support_email(notification):
    # Get new messages
    history = push.get_notification_history(...)

    for change in history['changes']:
        if change['type'] == 'message_added':
            # Read email
            email = client.read_emails(query=f"id:{change['message_id']}")

            # Create support ticket automatically
            ticket_id = support_system.create_ticket(
                subject=email['subject'],
                from_email=email['from'],
                body=email['body']
            )

            # Apply label
            client.apply_labels(
                message_ids=[change['message_id']],
                label_ids=["Support/In Progress"]
            )

            # Auto-reply
            client.send_email(
                to=[email['from']],
                subject=f"Re: {email['subject']}",
                body=f"Ticket #{ticket_id} created. We'll respond within 24 hours.",
                thread_id=email['thread_id']
            )
```

### Use Case 4: Draft Review Workflow

```python
# Manager creates proposal draft
draft_result = await email_advanced.execute(
    action="create_draft",
    account_name="sales",
    to=["bigclient@corp.com"],
    subject="Enterprise AI Solution Proposal",
    body="...",
    attachments=["proposals/enterprise_proposal_v1.pdf"]
)

# Team reviews draft (separate system)
# ...

# After approval, send draft
await email_advanced.execute(
    action="send_draft",
    account_name="sales",
    draft_id=draft_result['draft_id']
)

# Apply tracking labels
await email_advanced.execute(
    action="apply_labels",
    message_ids=[sent_message_id],
    label_ids=["Proposals/Enterprise", "Needs Follow-up"]
)
```

---

## 🧪 Testing

### Test OAuth2 Authentication

```bash
python3 -c "
from python.helpers.gmail_oauth2 import GmailOAuth2Handler
handler = GmailOAuth2Handler()
result = handler.authenticate_account(
    'test',
    'data/gmail_credentials/credentials.json'
)
print(result)
"
```

### Test Gmail API Read

```bash
python3 -c "
from python.helpers.gmail_api_client import GmailAPIClient
client = GmailAPIClient('test')
emails = client.read_emails(max_results=5)
for email in emails:
    print(f'{email[\"from\"]} - {email[\"subject\"]}')
"
```

### Test Push Notifications

```bash
python3 -c "
from python.helpers.gmail_push_notifications import GmailPushNotifications
push = GmailPushNotifications(project_id='your-project')
setup = push.setup_topic_and_subscription()
print(setup)
result = push.enable_push_notifications('test')
print(result)
"
```

---

## 🐛 Troubleshooting

### "OAuth2 libraries not installed"

```bash
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### "credentials.json not found"

- Download OAuth2 credentials from Google Cloud Console
- Save to `data/gmail_credentials/credentials.json`

### "Access denied" or "Insufficient permissions"

- Check OAuth2 scopes in `gmail_oauth2.py`
- Re-authenticate account to grant new permissions

### "Token expired"

- Tokens auto-refresh if refresh_token exists
- If failed, re-run authenticate action
- Check token file in `data/gmail_credentials/`

### "Pub/Sub not enabled"

- Enable Cloud Pub/Sub API in Google Cloud Console
- Ensure service account has Pub/Sub Editor role

### "Watch expired"

- Gmail watch expires after ~7 days
- Re-run enable_push action
- Implement auto-renewal (check expiration timestamp)

---

## 📈 Migration from Phase 1

### Gradual Migration Strategy

**Keep Phase 1 (SMTP) for:**

- Simple send operations
- Non-Gmail accounts
- Low-complexity workflows

**Migrate to Phase 2 (Gmail API) for:**

- Multi-account management
- Label organization
- Draft workflows
- Advanced search
- Threading support

**Example: Dual Support**

```python
# Simple send - use SMTP (Phase 1)
if simple_send:
    await email.send_email(to, subject, body)

# Advanced features - use Gmail API (Phase 2)
else:
    await email_advanced.send_gmail(
        account_name="sales",
        to=to,
        subject=subject,
        body=body,
        labels=["Important"],
        thread_id=reply_to_thread
    )
```

---

## 🔮 Future Enhancements

### Potential Phase 4 Features

- Calendar integration (schedule emails)
- Gmail filters automation
- Canned responses management
- Email templates with variables
- Attachment scanning and extraction
- Conversation threading visualization
- Email analytics and reporting
- AI-powered email classification
- Auto-response based on content
- Email deduplication

---

## 📝 Files Delivered

### Phase 2 Files

1. `python/helpers/gmail_oauth2.py` (271 lines) - OAuth2 handler
2. `python/helpers/gmail_api_client.py` (658 lines) - Gmail API client
3. `python/tools/email_advanced.py` (554 lines) - Advanced email tool

### Phase 3 Files

4. `python/helpers/gmail_push_notifications.py` (414 lines) - Pub/Sub integration

### Documentation

5. `docs/GMAIL_API_PHASE2_PHASE3.md` (this file)

**Total: ~1,900 lines of production code**

---

## ✅ Completion Checklist

**Phase 2:**

- [x] OAuth2 authentication handler
- [x] Multi-account management
- [x] Gmail API send with threading
- [x] Advanced email reading
- [x] Label creation and management
- [x] Draft creation and sending
- [x] Advanced search with filters
- [x] Account listing and status

**Phase 3:**

- [x] Google Pub/Sub integration
- [x] Topic and subscription setup
- [x] Enable/disable Gmail watch
- [x] Push notification handling
- [x] History retrieval
- [x] Webhook endpoint support
- [x] Callback registration
- [x] Signature verification

**Documentation:**

- [x] Complete usage guide
- [x] Setup instructions
- [x] Security considerations
- [x] Use case examples
- [x] Troubleshooting section
- [x] Testing procedures

---

## 🎉 Success

Phase 2 and Phase 3 implementation complete! You now have:

✅ **Multi-Account Gmail Management** (Phase 2)
✅ **Real-Time Push Notifications** (Phase 3)
✅ **Advanced Email Operations**
✅ **Comprehensive Documentation**

Ready to scale your email automation with enterprise-grade features!
