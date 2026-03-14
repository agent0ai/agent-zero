# Gmail UI Integration - Quick Reference

## 🎯 What's New

Agent Jumbo now supports **web-based Gmail account setup** through the Settings UI - no more manual credential file management!

## 📦 Files Created/Modified

### New API Endpoints (4 files, 9.6K)

```
python/api/
├── gmail_oauth_start.py      (2.2K) - Start OAuth2 flow
├── gmail_oauth_callback.py   (3.5K) - Handle OAuth2 redirect
├── gmail_accounts_list.py    (2.0K) - List all accounts
└── gmail_account_remove.py   (1.9K) - Remove accounts
```

### Updated Core Files (4 files)

```
python/helpers/
├── settings.py          - Added gmail_accounts field & UI section
├── gmail_oauth2.py      - Added web OAuth2 methods
└── runtime.py           - Added get_web_ui_host()

webui/js/
└── settings.js          - Added Gmail button handlers
```

### Documentation (4 files)

```
docs/
├── GMAIL_API_PHASE2_PHASE3.md         - Complete Gmail API guide
├── GMAIL_UI_SETUP.md                  - UI setup instructions
├── GMAIL_UI_INTEGRATION_SUMMARY.md    - Implementation details
└── GMAIL_UI_TESTING.md                - Testing plan
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### 2. Get Google OAuth2 Credentials

1. <https://console.cloud.google.com/> → New Project
2. Enable Gmail API
3. Create OAuth client ID (Web application)
4. Add redirect URI: `http://localhost:5000/gmail_oauth_callback`
5. Download `credentials.json`

### 3. Add Account (Two Options)

#### Option A: Via Settings UI

1. Settings → External tab → Gmail Accounts
2. Click "Manage Accounts"
3. Upload or paste `credentials.json` in the modal
4. Click "Authenticate via Google"

#### Option A2: Test & Setup Utility

1. Settings → External tab → Gmail Accounts
2. Click "Test & Setup Utility"
3. Follow the step-by-step OAuth + test email flow

#### Option B: Via API

```bash
curl -X POST http://localhost:5000/gmail_oauth_start \
  -H "Content-Type: application/json" \
  -d '{
    "account_name": "sales",
    "credentials_json": "PASTE_CREDENTIALS_JSON_HERE"
  }'
```

Response includes `authorization_url` (alias: `auth_url`) - open in browser to complete OAuth2 flow.

### 4. Use Account

```python
# In Agent Jumbo conversation
"Send email via Gmail to customer@example.com"

# Tool call (automatic)
{
    "action": "send_gmail",
    "account_name": "sales",  # Auto-selected or specify
    "to": ["customer@example.com"],
    "subject": "Hello",
    "body": "Message"
}
```

## 🔑 Key Features

### OAuth2 Web Flow

- ✅ No local server required
- ✅ Popup/redirect based authentication
- ✅ CSRF protection via state tokens
- ✅ Automatic token refresh

### Account Management

- ✅ Multiple accounts supported
- ✅ Status tracking (valid/expired)
- ✅ Persistent across restarts
- ✅ Easy removal

### Security

- ✅ Tokens stored in `data/gmail_credentials/` (pickled)
- ✅ Session-based CSRF protection
- ✅ Secure credential handling
- ✅ Auto-refresh expired tokens

## 📋 API Reference

### Start OAuth2

```http
POST /gmail_oauth_start
Content-Type: application/json

{
    "account_name": "sales",
    "credentials_json": "{...}"
}

Response: {
    "success": true,
    "authorization_url": "https://accounts.google.com/...",
    "state": "csrf_token"
}
```

### Send Test Email

```http
POST /gmail_test_send
Content-Type: application/json

{
    "account_name": "sales",
    "to": "you@example.com",
    "subject": "Agent Jumbo Gmail Test",
    "body": "This is a test email from Agent Jumbo Gmail UI."
}
```

### OAuth2 Callback

```http
GET /gmail_oauth_callback?code=AUTH_CODE&state=CSRF_TOKEN

Response: {
    "success": true,
    "account_name": "sales",
    "email": "sales@company.com"
}
```

### List Accounts

```http
POST /gmail_accounts_list

Response: {
    "success": true,
    "accounts": [{
        "name": "sales",
        "email": "sales@company.com",
        "authenticated": true,
        "valid": true,
        "expired": false
    }],
    "count": 1
}
```

### Remove Account

```http
POST /gmail_account_remove
Content-Type: application/json

{
    "account_name": "sales"
}

Response: {
    "success": true,
    "message": "Account 'sales' removed successfully"
}
```

## 🎨 Settings UI

Location: **Settings → External tab → Gmail Accounts**

### Fields

- **Account Info**: Shows count of configured accounts
- **Manage Accounts**: Opens account manager (lists accounts)
- **View Setup Guide**: Shows setup instructions

### Current UI (v1.0)

- Account list displayed in notifications
- Console logging for details
- Button-based actions

### Planned UI (v2.0)

- Full modal with account table
- Inline authentication buttons
- File upload for credentials.json
- Real-time status indicators

## 🔧 Configuration

### Settings Schema

```python
# In tmp/settings.json
{
    "gmail_accounts": {
        "sales": {
            "email": "sales@company.com",
            "authenticated": true,
            "scopes": [...]
        }
    }
}
```

### Token Storage

```
data/gmail_credentials/
├── token_sales.pickle
├── token_support.pickle
└── credentials.json (optional default)
```

### Environment Variables (Optional)

```bash
WEB_UI_HOST=localhost  # For OAuth2 redirect URI
WEB_UI_PORT=5000       # For OAuth2 redirect URI
```

## 🐛 Troubleshooting

### "Failed to start OAuth2 flow"

→ Check credentials.json is valid JSON
→ Verify redirect URI in Google Cloud Console

### "Invalid state token"

→ Don't navigate away during OAuth2 flow
→ Check browser allows cookies

### "Credentials expired"

→ Remove account: `POST /gmail_account_remove`
→ Re-authenticate with fresh flow

### "Module not found: google-auth-oauthlib"

→ Install dependencies: `pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client`

## 📊 Testing Status

✅ **Syntax Validated**

- All Python files compile successfully
- JavaScript syntax verified
- No import errors in modified files

⏳ **Pending Manual Testing**

- Full OAuth2 flow (requires Google Cloud setup)
- Account manager UI
- Multi-account workflows
- Token refresh on expiry

See `docs/GMAIL_UI_TESTING.md` for complete test plan.

## 🎯 Success Criteria

✅ Settings schema extended
✅ API endpoints created (4)
✅ OAuth2 web flow implemented
✅ UI components integrated
✅ Documentation complete (4 guides)
✅ Security measures in place
✅ Syntax validation passed

## 📚 Documentation

| File | Purpose |
|------|---------|
| `GMAIL_API_PHASE2_PHASE3.md` | Complete Gmail API documentation |
| `GMAIL_UI_SETUP.md` | Step-by-step UI setup guide |
| `GMAIL_UI_INTEGRATION_SUMMARY.md` | Implementation architecture |
| `GMAIL_UI_TESTING.md` | Comprehensive test plan |

## 🔄 Next Steps

1. **Test OAuth2 Flow**
   - Create Google Cloud project
   - Test end-to-end authentication

2. **Build Full Modal UI**
   - Replace notification-based display
   - Add account table with actions
   - File upload widget

3. **Enhance Tool Integration**
   - Add account dropdown to email_advanced
   - Auto-populate from settings
   - Show account status in tool UI

4. **Add Advanced Features**
   - Batch account import/export
   - Usage analytics
   - Account health dashboard

## 💡 Usage Examples

### Send Email

```
User: "Send email to john@example.com about the meeting"
Agent: Uses email_advanced with account_name="sales"
```

### Read Emails

```
User: "Check my unread emails from support@company.com"
Agent: {
    "action": "read_gmail",
    "account_name": "support",
    "query": "from:support@company.com is:unread"
}
```

### Manage Labels

```
User: "Create a label called 'Important Clients'"
Agent: {
    "action": "create_label",
    "account_name": "sales",
    "label_name": "Important Clients"
}
```

## 🎉 Summary

**What Changed:**

- ✅ 4 new API endpoints for OAuth2 flow
- ✅ Settings UI with Gmail Accounts section
- ✅ Web-compatible OAuth2 (no local server)
- ✅ Multiple account support
- ✅ Automatic token management

**What's Ready:**

- ✅ Production code (syntax validated)
- ✅ API handlers (auto-registered)
- ✅ Settings integration (persists data)
- ✅ Documentation (4 comprehensive guides)
- ✅ Testing plan (15 test cases)

**What's Next:**

- ⏳ Manual testing with Google Cloud
- ⏳ Full modal UI implementation
- ⏳ Enhanced tool integration
- ⏳ User feedback & iteration

---

**Ready to test!** Set up Google Cloud OAuth2 credentials and follow the Quick Start guide.

For questions or issues, see `docs/GMAIL_UI_TESTING.md` or check the Agent Jumbo documentation.
