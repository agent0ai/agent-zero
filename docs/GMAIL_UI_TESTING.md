# Gmail UI Integration - Testing Plan

## Pre-Test Setup

### 1. Install Dependencies

```bash
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client google-cloud-pubsub
```

### 2. Create Google Cloud Project

1. Go to <https://console.cloud.google.com/>
2. Create new project: `agent-jumbo-gmail`
3. Enable Gmail API:
   - APIs & Services → Library
   - Search "Gmail API" → Enable

4. Create OAuth2 Credentials:
   - APIs & Services → Credentials
   - Create Credentials → OAuth client ID
   - Application type: **Web application**
   - Name: `Agent Jumbo Gmail Integration`
   - Authorized redirect URIs:

     ```
     http://localhost:5000/gmail_oauth_callback
     http://127.0.0.1:5000/gmail_oauth_callback
     ```

   - Download `credentials.json`

### 3. Start Agent Jumbo

```bash
python run_ui.py
```

## Test Cases

### Test 1: Settings UI Display ✓

**Steps:**

1. Open Agent Jumbo UI (<http://localhost:5000>)
2. Click Settings icon
3. Navigate to "External" tab
4. Scroll to "Gmail Accounts" section

**Expected Results:**

- ✓ "Gmail Accounts" section visible
- ✓ Shows "Currently configured accounts: 0"
- ✓ "Manage Accounts" button present
- ✓ "View Setup Guide" button present

### Test 2: Setup Guide Display ✓

**Steps:**

1. In Gmail Accounts section
2. Click "View Setup Guide" button

**Expected Results:**

- ✓ Notification appears with setup instructions
- ✓ Console shows formatted guide text
- ✓ References `docs/GMAIL_API_PHASE2_PHASE3.md`

### Test 3: Account List (Empty State) ✓

**Steps:**

1. Click "Manage Accounts" button

**Expected Results:**

- ✓ Notification shows "Gmail Accounts (0)"
- ✓ Message: "No accounts configured"
- ✓ Console logs empty accounts array

### Test 4: OAuth2 Flow - Start

**Steps:**

1. Make POST request to `/gmail_oauth_start`:

   ```bash
   curl -X POST http://localhost:5000/gmail_oauth_start \
     -H "Content-Type: application/json" \
     -H "X-CSRF-Token: YOUR_CSRF_TOKEN" \
     -b "session_cookie" \
     -d '{
       "account_name": "test",
       "credentials_json": "PASTE_CREDENTIALS_JSON_CONTENT_HERE"
     }'
   ```

**Expected Results:**

- ✓ Response contains `authorization_url` (alias: `auth_url`)
- ✓ Response contains `state` token
- ✓ `authorization_url` points to accounts.google.com
- ✓ Session stores oauth state

**Alternative (Browser Console):**

```javascript
fetch('/gmail_oauth_start', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': document.cookie.split('csrf_token_')[1]?.split(';')[0]
    },
    body: JSON.stringify({
        account_name: 'test',
        credentials_json: 'PASTE_JSON_HERE'
    })
}).then(r => r.json()).then(console.log);
```

### Test 5: OAuth2 Flow - Complete

**Steps:**

1. Open `authorization_url` from Test 4 in browser
2. Sign in with Gmail account
3. Grant permissions
4. Observe redirect to `/gmail_oauth_callback`

**Expected Results:**

- ✓ Redirected to callback URL with `code` and `state` params
- ✓ State token verified
- ✓ Credentials saved to `data/gmail_credentials/token_test.pickle`
- ✓ Account added to settings
- ✓ Success message displayed
- ✓ Email address shown

### Test 6: Account List (With Accounts)

**Steps:**

1. After completing Test 5
2. Click "Manage Accounts" button again

**Expected Results:**

- ✓ Notification shows "Gmail Accounts (1)"
- ✓ Shows account name: "test"
- ✓ Shows email address
- ✓ Status: "Valid"
- ✓ Console shows full account details

### Test 7: Test Utility (UI Flow)

**Steps:**

1. In Settings → External → Gmail Accounts, click "Test & Setup Utility"
2. Complete Step 1 OAuth flow (reuse credentials from Test 4)
3. Refresh accounts in Step 2
4. Send a test email in Step 3

**Expected Results:**

- ✓ OAuth popup opens and completes
- ✓ Account appears in account list
- ✓ Test email sends successfully

### Test 8: Account Status Check

**Steps:**

```bash
curl -X POST http://localhost:5000/gmail_accounts_list \
  -H "Content-Type: application/json" \
  -b "session_cookie"
```

**Expected Results:**

```json
{
    "success": true,
    "accounts": [
        {
            "name": "test",
            "email": "your-email@gmail.com",
            "authenticated": true,
            "valid": true,
            "expired": false,
            "scopes": ["https://www.googleapis.com/auth/gmail.readonly", ...],
            "error": null
        }
    ],
    "count": 1
}
```

### Test 9: Use Account in Email Tool

**Steps:**

1. Send message to Agent Jumbo:

   ```
   Send an email using Gmail to test@example.com with subject "Test" and body "Hello"
   ```

2. Agent should use `email_advanced` tool:

   ```json
   {
       "action": "send_gmail",
       "account_name": "test",
       "to": ["test@example.com"],
       "subject": "Test",
       "body": "Hello"
   }
   ```

**Expected Results:**

- ✓ Email sent successfully
- ✓ No authentication errors
- ✓ Credentials auto-loaded from settings

### Test 10: Account Removal

**Steps:**

```bash
curl -X POST http://localhost:5000/gmail_account_remove \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: YOUR_CSRF_TOKEN" \
  -b "session_cookie" \
  -d '{"account_name": "test"}'
```

**Expected Results:**

- ✓ Response: `{"success": true, "message": "Account 'test' removed successfully"}`
- ✓ Token file deleted: `data/gmail_credentials/token_test.pickle`
- ✓ Account removed from settings
- ✓ Account list shows 0 accounts

### Test 11: Multiple Accounts

**Steps:**

1. Add account "sales" via OAuth2 flow
2. Add account "support" via OAuth2 flow
3. Check account list

**Expected Results:**

- ✓ Both accounts listed
- ✓ Each has unique email address
- ✓ Both show as authenticated
- ✓ Can use either account in email tool

### Test 12: Token Refresh

**Steps:**

1. Manually expire token (set expiry to past in pickle file)
2. Use account in email tool
3. Check token file updated

**Expected Results:**

- ✓ Token automatically refreshed
- ✓ Email sent successfully
- ✓ New expiry time in token file
- ✓ No re-authentication required

### Test 13: Error Handling - Invalid Credentials

**Steps:**

1. Start OAuth2 with invalid credentials.json

   ```json
   {"credentials_json": "invalid json"}
   ```

**Expected Results:**

- ✓ Error response returned
- ✓ No credentials saved
- ✓ Helpful error message

### Test 14: Error Handling - Expired Session

**Steps:**

1. Start OAuth2 flow
2. Clear browser cookies
3. Complete OAuth2 callback

**Expected Results:**

- ✓ Error: "Session expired or invalid"
- ✓ No credentials saved
- ✓ User instructed to retry

### Test 15: CSRF Protection

**Steps:**

1. Start OAuth2 flow (get state token)
2. Manually call callback with different state:

   ```
   /gmail_oauth_callback?code=test&state=wrong_token
   ```

**Expected Results:**

- ✓ Error: "Invalid state token (CSRF protection)"
- ✓ No credentials saved
- ✓ Security violation logged

### Test 16: Settings Persistence

**Steps:**

1. Add Gmail account
2. Restart Agent Jumbo (`Ctrl+C`, then `python run_ui.py`)
3. Check account list

**Expected Results:**

- ✓ Account still present in settings
- ✓ Token file still exists
- ✓ Account functional after restart

## Performance Tests

### P1: OAuth2 Flow Speed

- Start flow → Auth URL generation: < 1 second
- Complete flow → Save credentials: < 2 seconds

### P2: Account List Load

- Load 10 accounts: < 1 second
- Each status check: < 500ms

### P3: Settings UI Load

- Gmail section render: < 100ms
- Account count update: Immediate

## Security Tests

### S1: Token File Permissions

```bash
ls -la data/gmail_credentials/
```

- ✓ Files readable only by current user
- ✓ Directory not world-accessible

### S2: Session Storage

- ✓ State token in session, not exposed to client
- ✓ credentials.json cleared after auth
- ✓ Session cookie has Secure flag (if HTTPS)

### S3: OAuth2 Scope Validation

- ✓ Only requested scopes granted
- ✓ No excessive permissions
- ✓ Scopes match SCOPES constant

## Cleanup After Testing

```bash
# Remove test credentials
rm -rf data/gmail_credentials/

# Reset settings
rm tmp/settings.json

# Or remove specific account
curl -X POST http://localhost:5000/gmail_account_remove \
  -d '{"account_name": "test"}'
```

## Known Limitations

1. **No Modal UI Yet**
   - Account manager uses notifications
   - Future: Full modal with account table

2. **Manual credentials.json Upload**
   - Currently paste JSON string
   - Future: File upload widget

3. **No Bulk Operations**
   - Add/remove one account at a time
   - Future: Batch import/export

4. **Basic Error Messages**
   - Console logging for details
   - Future: Rich error UI with retry options

## Success Criteria

All ✓ items must pass:

- ✓ Settings UI displays correctly
- ✓ OAuth2 flow completes successfully
- ✓ Accounts persist across restarts
- ✓ Email tool uses authenticated accounts
- ✓ Account removal works
- ✓ CSRF protection active
- ✓ Token refresh automatic
- ✓ Multiple accounts supported

## Bug Reports Template

```markdown
### Issue Description
[What went wrong]

### Steps to Reproduce
1. [First step]
2. [Second step]
3. [Result]

### Expected Behavior
[What should happen]

### Actual Behavior
[What actually happened]

### Environment
- Agent Jumbo version: [git commit hash]
- Python version: [3.x.x]
- Browser: [Chrome/Firefox/etc]
- OS: [Linux/Windows/Mac]

### Logs
[Console output, error messages]
```

## Next Steps After Testing

1. Fix any bugs found
2. Implement full modal UI for account manager
3. Add file upload for credentials.json
4. Create account status dashboard
5. Add batch operations support
6. Integrate with email_advanced tool schema
