# DAV MCP Server

Access your calendars, contacts, and files via MCP!

<a href="https://glama.ai/mcp/servers/@jahfer/dav-mcp-server">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/@jahfer/dav-mcp-server/badge" alt="DAV Server MCP server" />
</a>

## Introduction

This project is a Model Context Protocol (MCP) server that allows you to interact with your CalDAV, CardDAV, and WebDAV services. It supports both Fastmail and Apple iCloud accounts, configured via environment variables.

## Setup

1.  **Prerequisites**: Ensure you have Node.js installed.
2.  **Clone the repository**: Clone this repository to your local machine.
3.  **Install dependencies**: Navigate to the project directory and run:

    ```bash
    npm install
    ```

    If you intend to publish or use this as a global command, you might also run `npm link` after installation, or install it globally via `npm install -g .` (once `package.json` is configured for global installation if desired).

## Environment Variable Configuration

To connect to your DAV services, you need to set the following environment variables when running the application:

- `DAV_PROVIDER`: Specifies your DAV service provider. Set to `fastmail` or `icloud` (case-insensitive).
- `DAV_USERNAME`: Your username for the service (e.g., your Fastmail email address or Apple ID).
- `DAV_PASSWORD`: An app-specific password for the service. It is highly recommended to use app-specific passwords for security.

## MCP Configuration

To use this server, you need to configure it as an `mcpServer` in your MCP configuration file. Here is an example:

```jsonc
{
  "mcpServers": {
    "myDavServices": {
      // You can name this anything you like
      "command": "npx", // Or simply "node" if it's in your PATH
      "args": ["-y", "@jahfer/dav-mcp-server"], // Path to the main script
      "env": {
        "DAV_PROVIDER": "icloud", // or "fastmail"
        "DAV_USERNAME": "your-username",
        "DAV_PASSWORD": "your-app-specific-password"
      }
    }
  }
}
```

## Available Tools

Once configured, this MCP server provides the following tools:

### Calendar (CalDAV)

- `get_my_calendars`: Lists all your available calendars.
- `get_calendar_events`: Fetches events from a specified calendar. You can optionally provide a start and end date/time to filter events within a specific range.

### Contacts (CardDAV)

- `get_my_contact_lists`: Lists all your contact address books.
- `get_contacts_from_list`: Fetches contacts from a specified address book.

### Files (WebDAV - primarily for Fastmail)

- `list_my_files_and_folders`: Lists files and folders within a specified path in your WebDAV storage (defaults to the root).
- `get_file_or_folder_details`: Fetches metadata for a given file or folder URL.

## Usage

After setting up the MCP server in your configuration, you can use commands or features within your MCP client that interact with the server definition to manage your calendars, contacts, and files.