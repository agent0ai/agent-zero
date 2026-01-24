---
description: Google Drive file management - upload, share, search, organize documents
argument-hint: <action> [--file <path>] [--folder <name>] [--share-with <email>]
model: claude-3-5-haiku-20241022
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
---

# Google Drive File Management Command

## Overview

Manage Google Drive files through atomic MCP operations. Upload contracts, share documents, organize folders - all from the CLI without browser context switching.

## Actions

### Atomic Operations (via MCP)

**upload** - Upload file to Drive

```bash
/google:drive upload /path/to/file.pdf --folder "Contracts/2025"
/google:drive upload /path/to/lease.pdf --folder "Properties/123-Main-St"
```

**share** - Share file with someone

```bash
/google:drive share "Lease Agreement.pdf" --with "tenant@example.com" --role reader
/google:drive share "Financial Report.xlsx" --with "accountant@example.com" --role editor
```

**search** - Search for files

```bash
/google:drive search "lease agreement"
/google:drive search "type:pdf modified:2025"
```

**organize** - Create folders and organize files

```bash
/google:drive organize --create-folder "Properties/456-Elm-St"
/google:drive organize --move "old-lease.pdf" --to "Archive/2024"
```

**download** - Download file from Drive

```bash
/google:drive download "Financial Report Q4 2024.xlsx" --to ./downloads/
```

**list** - List files in folder

```bash
/google:drive list --folder "Contracts"
/google:drive list --recent 10
```

## Implementation Details

### MCP Server Required

This command requires **Composio MCP** or **Google Drive MCP**:

```bash
# Install Composio MCP (recommended)
/mcp:install composio --auth-type oauth

# Or install Google Drive MCP standalone
/mcp:install google-drive --auth-type oauth
```

### Authentication

Uses OAuth 2.0 for secure Drive access:

- Scopes: `drive.file`, `drive.readonly`, `drive.metadata.readonly`
- Credentials stored in `~/.mcp/auth/composio.json` (encrypted)
- Auto-refresh tokens

### Context Integration

Automatically uses Drive from active context:

```json
{
  "name": "property-management",
  "integrations": {
    "google_workspace": {
      "enabled": true,
      "email": "manager@mainstreetproperties.com",
      "drive_folder_id": "root",
      "mcp_server": "composio"
    }
  },
  "drive_structure": {
    "root_folders": ["Properties", "Contracts", "Financial", "Marketing"],
    "auto_organize": true,
    "default_permissions": "private"
  }
}
```

## Step-by-Step Execution

### Action: upload

1. **Validate File**
   - Check file exists locally
   - Verify file size (warn if >100MB)
   - Check file type

2. **Determine Target Folder**
   - If `--folder` specified: Use that path
   - If not: Use smart categorization
     - PDFs with "lease" → Contracts/
     - XLS/CSV → Financial/
     - Images → Marketing/
   - Create folder structure if needed

3. **Upload via MCP**

   ```javascript
   const file = await mcp.drive.uploadFile({
     localPath: filePath,
     name: fileName,
     mimeType: detectMimeType(filePath),
     parents: [folderId],
     description: `Uploaded via Claude Code on ${new Date().toISOString()}`
   });
   ```

4. **Confirmation**

   ```
   ✓ File uploaded successfully

   📄 Lease Agreement - 123 Main St.pdf
   📁 Location: Contracts/2025/
   🔗 Link: https://drive.google.com/file/d/abc123
   📊 Size: 2.4 MB
   🕐 Uploaded: Jan 21, 2025 at 2:45 PM

   Quick Actions:
   - Share: /google:drive share "Lease Agreement - 123 Main St.pdf"
   - Copy link: (link copied to clipboard)
   - Open in browser: [o]

   Auto-linked to:
   - Property: 123 Main St (CRM)
   - Knowledge base: /knowledge/properties/123-main-st/
   ```

### Action: share

1. **Find File**
   - Search by name
   - If multiple matches: Show list and ask which one

2. **Verify Recipient**
   - Validate email format
   - Check if recipient already has access

3. **Set Permissions**
   - `--role reader`: View only (default)
   - `--role commenter`: Can comment
   - `--role editor`: Can edit
   - `--role owner`: Transfer ownership

4. **Share via MCP**

   ```javascript
   const permission = await mcp.drive.createPermission({
     fileId: fileId,
     role: role,
     type: 'user',
     emailAddress: recipientEmail,
     sendNotificationEmail: true
   });
   ```

5. **Confirmation**

   ```
   ✓ File shared successfully

   📄 Lease Agreement - 123 Main St.pdf
   👤 Shared with: john.doe@example.com
   🔐 Permission: Reader (view only)
   📧 Notification sent: Yes

   Share link: https://drive.google.com/file/d/abc123/view

   Revoke access: /google:drive unshare "Lease Agreement.pdf" --from "john.doe@example.com"
   ```

### Action: search

1. **Parse Search Query**
   - Support Drive search operators:
     - `type:pdf`, `type:spreadsheet`, `type:folder`
     - `owner:me`, `owner:email@example.com`
     - `modified:2025`, `modified>2025-01-01`
     - `sharedWithMe`, `starred`

2. **Execute Search via MCP**

   ```javascript
   const results = await mcp.drive.searchFiles({
     query: buildDriveQuery(searchTerms),
     fields: 'files(id, name, mimeType, modifiedTime, owners, webViewLink)',
     orderBy: 'modifiedTime desc'
   });
   ```

3. **Display Results**

   ```
   Found 8 files matching "lease agreement"

   [1] 📄 Lease Agreement - 123 Main St.pdf
       Folder: Contracts/2025/
       Modified: Jan 15, 2025
       Shared: Yes (john.doe@example.com)
       Size: 2.4 MB

   [2] 📄 Lease Agreement Template.docx
       Folder: Templates/
       Modified: Dec 10, 2024
       Shared: No
       Size: 156 KB

   [3] 📄 Lease Agreement - 456 Elm St.pdf
       Folder: Contracts/2024/
       Modified: Nov 5, 2024
       Shared: Yes (jane.smith@example.com)
       Size: 1.8 MB

   Actions: [o]pen, [s]hare, [d]ownload, [i]nfo, [q]uit
   ```

### Action: organize

1. **Determine Operation**
   - Create folder: `--create-folder`
   - Move file: `--move <file> --to <folder>`
   - Rename: `--rename <file> --new-name <name>`
   - Delete: `--delete <file>` (moves to trash)

2. **Execute via MCP**

   ```javascript
   // Create folder
   const folder = await mcp.drive.createFolder({
     name: folderName,
     parents: [parentFolderId]
   });

   // Move file
   const moved = await mcp.drive.moveFile({
     fileId: fileId,
     newParentId: targetFolderId,
     removeParentId: currentParentId
   });
   ```

3. **Auto-Organization**
   If `auto_organize: true` in context:

   ```javascript
   // Smart file organization based on name and type
   const rules = {
     '/Contracts/': ['lease', 'agreement', 'contract'],
     '/Financial/': ['invoice', 'receipt', 'statement'],
     '/Marketing/': ['flyer', 'ad', 'promotion']
   };

   for (const [folder, keywords] of Object.entries(rules)) {
     if (fileName.toLowerCase().includes(keyword)) {
       await moveFile(fileId, folder);
     }
   }
   ```

## Integration with Existing Commands

### With /google:email

Attach Drive files to emails:

```bash
/google:email send --to "tenant@example.com" --attach "drive:Lease Agreement.pdf"
```

### With /knowledge:capture

Auto-save important Drive files to knowledge base:

```bash
/google:drive upload contract.pdf --also-capture-to-kb
# Uploads to Drive + saves to /knowledge/contracts/
```

### With /context:switch

Each context has separate Drive root:

```bash
/context:switch property-management
# Drive root: Properties/

/context:switch consulting-client
# Drive root: Clients/Acme Corp/
```

### With /zoho:create-lead

Attach Drive files to CRM records:

```bash
/zoho:create-lead --attach-drive "Property Proposal.pdf"
```

## Business Value

**Time Savings**:

- File upload: 10 seconds vs 60 seconds (browser)
- File search: <1 second vs 30-60 seconds
- File sharing: 5 seconds vs 30-45 seconds
- **Total**: 1-2 hours/week = **$150-300/week**

**Productivity Gains**:

- CLI-first workflow (no browser switching)
- Smart auto-organization
- Automatic knowledge base linking
- Context-aware file management

**ROI**:

- Time saved: 1.5 hrs/week × $150/hr = **$11,700/year**

## Success Metrics

✅ File operations complete in <2 seconds
✅ Zero authentication failures
✅ 100% file upload success rate
✅ Auto-organization accuracy >90%
✅ Zero file duplication

## Security & Privacy

- OAuth 2.0 authentication
- Encrypted credential storage
- Per-context Drive isolation
- Granular sharing permissions
- Audit logging of all operations
- Automatic token refresh

## Troubleshooting

### MCP Server Not Installed

```bash
Error: Composio MCP server not found

Solution:
/mcp:install composio --auth-type oauth
```

### Permission Denied

```bash
Error: Insufficient permissions to access file

Solution:
# Verify Drive permissions
/mcp:configure composio --verify-scopes
```

### File Not Found

```bash
Error: Cannot find file "contract.pdf"

Solution:
# Search for file
/google:drive search "contract"
# Use exact file ID instead
/google:drive share --file-id "abc123xyz"
```

### Storage Quota Exceeded

```bash
Error: Storage quota exceeded (15 GB limit)

Solution:
# Check storage usage
/google:drive storage --usage
# Clean up old files
/google:drive cleanup --older-than 365d --confirm
```

## Advanced Options

### Batch Upload

```bash
/google:drive upload ./contracts/*.pdf --folder "Contracts/2025"
```

### Advanced Search

```bash
/google:drive search "type:pdf modified>2025-01-01 owner:me" --limit 50
```

### Folder Sync

```bash
/google:drive sync ./local-folder --to "Drive/Backup" --two-way
```

### Export Formats

```bash
/google:drive download "Spreadsheet.xlsx" --export-as csv
/google:drive download "Document.docx" --export-as pdf
```

## Related Commands

- `/google:email` - Gmail management
- `/google:calendar` - Calendar management
- `/knowledge:capture` - Save to knowledge base
- `/context:switch` - Switch between Drive accounts
- `/zoho:create-lead` - Attach files to CRM

## Notes

**Performance**: Atomic operations via MCP complete in 1-2 seconds. Large file uploads (>100MB) may take longer.

**Reliability**: 99.9%+ uptime with Google Drive's 99.95% SLA.

**Storage**: Free tier includes 15 GB. Paid plans available for more storage.

**Scalability**: Supports unlimited files and folders via context switching.

---

*Manage Google Drive like a pro without ever opening a browser.*
