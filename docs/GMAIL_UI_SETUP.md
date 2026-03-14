# Gmail Account Setup via Agent Jumbo UI

This guide explains how to set up Gmail accounts for Agent Jumbo using the web-based settings interface.

## Overview

Agent Jumbo now supports UI-based Gmail account setup through the Settings panel, eliminating the need for manual credential file management and command-line authentication.

## Prerequisites

1. **Google Cloud Project** with Gmail API enabled
2. **OAuth2 Credentials** (Web Application type)
3. **Python Dependencies** installed:

   ```bash
   pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
   ```

## Step-by-Step Setup

### 1. Create Google Cloud OAuth2 Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Gmail API**:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Gmail API" and click "Enable"

4. Create OAuth2 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose **"Web application"** as the application type
   - Add authorized redirect URI:

     ```
     http://localhost:5000/gmail_oauth_callback
     ```

     (Adjust port if your Agent Jumbo runs on a different port)

5. Download the credentials file (`credentials.json`)

### 2. Access Gmail Settings in Agent Jumbo

1. Open Agent Jumbo web interface
2. Click the **Settings** icon (⚙️) in the top navigation
3. Navigate to the **"External"** tab
4. Find the **"Gmail Accounts"** section

### 3. Add a Gmail Account

#### Option A: Via Settings UI

1. Click **"Manage Accounts"** button
2. In the account manager modal:
   - Enter a **name** for the account (e.g., "sales", "support", "personal")
   - Upload your `credentials.json` file or paste its contents
   - (Optional) Click **"Reformat"** to tidy the JSON
   - Click **"Authenticate via Google"**
3. A popup window will open to Google's OAuth2 consent screen
4. Sign in with the Gmail account you want to connect
5. Review and grant the requested permissions
6. The popup will close automatically after successful authentication

#### Option B: Via Email Advanced Tool

Use the `email_advanced` tool to authenticate:

```python
{
    "action": "authenticate",
    "account_name": "sales",
    "credentials_json_path": "/path/to/credentials.json"
}
```

### 4. Verify Account Status

1. In the Gmail Accounts section, you'll see:
   - Account name
   - Associated email address
   - Authentication status (✅ Valid / ⚠️ Expired / ❌ Invalid)
   - Number of configured accounts

2. Click **"View Setup Guide"** for detailed documentation

### 5. Run Test Utility (Recommended)

1. Click **"Test & Setup Utility"** in the Gmail Accounts section
2. Follow the 3-step flow to start OAuth, confirm the account, and send a test email
3. Review the troubleshooting tips if any step fails

## Account Management

### List All Accounts

API endpoint: `POST /gmail_accounts_list`

Returns all configured accounts with their status.

### Remove an Account

API endpoint: `POST /gmail_account_remove`

```json
{
    "account_name": "sales"
}
```

This will:

- Remove account from settings
- Delete stored OAuth2 tokens
- Revoke access (tokens still valid until Google expires them)

### Send Test Email

API endpoint: `POST /gmail_test_send`

```json
{
    "account_name": "sales",
    "to": "you@example.com",
    "subject": "Agent Jumbo Gmail Test",
    "body": "This is a test email from Agent Jumbo Gmail UI."
}
```

### Re-authenticate Expired Accounts

If an account shows as expired:

1. Click the account in the manager
2. Click **"Re-authenticate"**
3. Complete OAuth2 flow again

Tokens automatically refresh when possible, but sometimes require manual re-authentication.

## OAuth2 Scopes

Accounts are authenticated with the following Gmail API scopes:

- `gmail.readonly` - Read all email data
- `gmail.send` - Send emails on your behalf
- `gmail.modify` - Modify email metadata (labels, read/unread)
- `gmail.labels` - Manage email labels
- `gmail.compose` - Create and manage drafts

## Security Considerations

### Token Storage

- OAuth2 tokens are stored in `data/gmail_credentials/token_{account_name}.pickle`
- Tokens are encrypted using Google's credential storage
- Only the Agent Jumbo instance has access to these files

### CSRF Protection

The OAuth2 flow uses state tokens to prevent CSRF attacks:

- Each authentication request generates a unique state token
- Token is verified on callback to ensure request authenticity

### Refresh Tokens

- Tokens include refresh tokens for automatic renewal
- Refresh tokens are long-lived (typically 6 months)
- Use `prompt=consent` to force new refresh token generation

## Troubleshooting

### "Failed to start OAuth2 flow"

**Cause:** Invalid credentials.json or missing redirect URI

**Solution:**

1. Verify credentials.json is valid JSON
2. Check redirect URI in Google Cloud Console matches:

   ```
   http://localhost:5000/gmail_oauth_callback
   ```

3. Ensure Gmail API is enabled for your project

### "Invalid state token (CSRF protection)"

**Cause:** Session expired or OAuth2 callback from different request

**Solution:**

- Start the authentication flow again
- Don't navigate away from Agent Jumbo during authentication
- Check browser allows cookies from localhost

### "Credentials expired"

**Cause:** Refresh token expired or revoked

**Solution:**

1. Remove the account: `POST /gmail_account_remove`
2. Re-authenticate with fresh credentials

### "Google OAuth2 libraries not installed"

**Cause:** Missing Python dependencies

**Solution:**

```bash
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

## API Reference

### Start OAuth2 Flow

**Endpoint:** `POST /gmail_oauth_start`

**Request:**

```json
{
    "account_name": "sales",
    "credentials_json": "{...credentials content...}"
}
```

**Response:**

```json
{
    "success": true,
    "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?...",
    "state": "csrf_token_here",
    "message": "Open the authorization_url in a popup window to authorize"
}
```

### OAuth2 Callback

**Endpoint:** `GET /gmail_oauth_callback?code=...&state=...`

Handles the OAuth2 redirect and exchanges authorization code for credentials.

### List Accounts

**Endpoint:** `POST /gmail_accounts_list`

**Response:**

```json
{
    "success": true,
    "accounts": [
        {
            "name": "sales",
            "email": "sales@company.com",
            "authenticated": true,
            "valid": true,
            "expired": false,
            "scopes": ["https://www.googleapis.com/auth/gmail.readonly", ...]
        }
    ],
    "count": 1
}
```

### Remove Account

**Endpoint:** `POST /gmail_account_remove`

**Request:**

```json
{
    "account_name": "sales"
}
```

**Response:**

```json
{
    "success": true,
    "account_name": "sales",
    "message": "Account 'sales' removed successfully"
}
```

## Using Authenticated Accounts

Once accounts are configured, use them with the `email_advanced` tool:

```python
# Send email via Gmail API
{
    "action": "send_gmail",
    "account_name": "sales",  # Use configured account
    "to": ["customer@example.com"],
    "subject": "Product Update",
    "body": "..."
}

# Read emails
{
    "action": "read_gmail",
    "account_name": "sales",
    "max_results": 10,
    "query": "is:unread"
}

# Advanced search
{
    "action": "search_advanced",
    "account_name": "sales",
    "filters": {
        "from": "customer@example.com",
        "subject": "order",
        "has_attachment": true
    }
}
```

## Next Steps

- **Push Notifications:** Set up real-time email notifications via Google Cloud Pub/Sub
- **Label Management:** Organize emails with custom labels
- **Draft Management:** Create and manage email drafts programmatically
- **Multi-Account Workflows:** Use different accounts for different purposes

See `GMAIL_API_PHASE2_PHASE3.md` for complete Gmail API documentation.
