#!/usr/bin/env node

const { McpServer } = require("@modelcontextprotocol/sdk/server/mcp.js");
const { StdioServerTransport } = require("@modelcontextprotocol/sdk/server/stdio.js");
const { z } = require("zod");
const { DAVClient } = require("tsdav");

// Environment variables for DAV provider and credentials
const DAV_PROVIDER = (process.env.DAV_PROVIDER || "custom").toLowerCase(); // e.g. "fastmail" or "icloud"
const DAV_USERNAME = process.env.DAV_USERNAME || "";
const DAV_PASSWORD = process.env.DAV_PASSWORD || ""; // App-specific password
const CALDAV_URL = process.env.CALDAV_URL || "";
const CARDDAV_URL = process.env.CARDDAV_URL || "";

if (!DAV_USERNAME || !DAV_PASSWORD) {
  console.error("Error: DAV_USERNAME and DAV_PASSWORD environment variables are required.");
  process.exit(1);
}

let calDavServerUrl, cardDavServerUrl, webDavServerUrl;
let davClient, cardDavClient, webDavClient;

const server = new McpServer({
  name: `DAV MCP (${DAV_PROVIDER})`,
  version: "0.1.0"
});

// Precedence: explicit URLs override provider-derived URLs
calDavServerUrl = CALDAV_URL || null;
cardDavServerUrl = CARDDAV_URL || null;
webDavServerUrl = null;

// Provider-derived defaults if not explicitly set via CALDAV_URL/CARDDAV_URL
if (DAV_PROVIDER === "fastmail") {
  if (!calDavServerUrl) {
    calDavServerUrl = `https://caldav.fastmail.com/dav/principals/user/${DAV_USERNAME}/`;
  }
  if (!cardDavServerUrl) {
    cardDavServerUrl = `https://carddav.fastmail.com/dav/principals/user/${DAV_USERNAME}/`;
  }
  webDavServerUrl = `https://webdav.fastmail.com/dav/principals/user/${DAV_USERNAME}/`;
} else if (DAV_PROVIDER === "icloud") {
  if (!calDavServerUrl) {
    calDavServerUrl = "https://caldav.icloud.com";
  }
  if (!cardDavServerUrl) {
    cardDavServerUrl = "https://contacts.icloud.com";
  }
  webDavServerUrl = null; // iCloud Drive WebDAV is not directly supported here
} else if (!calDavServerUrl && !cardDavServerUrl) {
  console.warn(
    `Warning: Unsupported or unspecified DAV_PROVIDER "${DAV_PROVIDER}". ` +
      "Set CALDAV_URL and/or CARDDAV_URL to enable calendar/contacts. WebDAV tools will be unavailable."
  );
}

// Initialize clients based on resolved URLs
if (calDavServerUrl) {
  davClient = new DAVClient({
    serverUrl: calDavServerUrl,
    credentials: { username: DAV_USERNAME, password: DAV_PASSWORD },
    authMethod: "Basic",
    defaultAccountType: "caldav",
  });
}

if (cardDavServerUrl) {
  cardDavClient = new DAVClient({
    serverUrl: cardDavServerUrl,
    credentials: { username: DAV_USERNAME, password: DAV_PASSWORD },
    authMethod: "Basic",
    defaultAccountType: "carddav",
  });
}

if (webDavServerUrl) {
  webDavClient = new DAVClient({
    serverUrl: webDavServerUrl,
    credentials: { username: DAV_USERNAME, password: DAV_PASSWORD },
    authMethod: "Basic",
  });
}

server.tool(
  `get_my_${DAV_PROVIDER}_calendars`,
  {
    description: `Lists all available calendars from your ${DAV_PROVIDER} account. It returns a list of calendar objects, each containing details like its URL, name, and other properties. Use this to find the \`calendarUrl\` for other calendar-related tools.`,
    inputSchema: {}
  },
  async () => {
    if (!davClient) return { content: [{ type: "text", text: "CalDAV client not initialized for this provider."}], isError: true };
    try {
      await davClient.login();
      const calendars = await davClient.fetchCalendars();
      return {
        content: [{
          type: "text",
          text: JSON.stringify(calendars, null, 2)
        }]
      };
    } catch (error) {
      console.error(`Error in get_my_${DAV_PROVIDER}_calendars:`, error);
      return {
        content: [{
          type: "text",
          text: `Error listing calendars: ${JSON.stringify(error.message || error)}`
        }],
        isError: true
      };
    }
  }
);

server.tool(
  `get_calendar_events_from_${DAV_PROVIDER}`,
  {
    description: `Fetches events from a specific calendar. You must provide a \`calendarUrl\`, which you can get from the \`get_my_${DAV_PROVIDER}_calendars\` tool. You can also optionally specify a \`timeRangeStart\` and \`timeRangeEnd\` (in ISO 8601 format) to filter events within a specific time window. If no time range is given, it may fetch all events.`,
    inputSchema: {
      calendarUrl: z.string().describe("The unique identifier (URL) of the calendar from which to fetch events. You can get this from 'get_my_calendars'."),
      timeRangeStart: z.string().datetime().optional().describe("ISO 8601 datetime for start of range"),
      timeRangeEnd: z.string().datetime().optional().describe("ISO 8601 datetime for end of range"),
    },
  },
  async ({ calendarUrl, timeRangeStart, timeRangeEnd }) => {
    if (!davClient) return { content: [{ type: "text", text: "CalDAV client not initialized for this provider."}], isError: true };
    try {
      await davClient.login();
      const calendars = await davClient.fetchCalendars(); // Needed to find the calendar object
      const calendar = calendars.find(cal => cal.url === calendarUrl);

      if (!calendar) {
        return {
          content: [{ type: "text", text: `Error: Calendar with URL ${calendarUrl} not found.` }],
          isError: true
        };
      }

      const fetchOptions = { calendar };
      if (timeRangeStart && timeRangeEnd) {
        fetchOptions.timeRange = { start: timeRangeStart, end: timeRangeEnd };
      }

      const calendarObjects = await davClient.fetchCalendarObjects(fetchOptions);
      return {
        content: [{
          type: "text",
          text: JSON.stringify(calendarObjects, null, 2)
        }]
      };
    } catch (error) {
      console.error("Error in get_calendar_events:", error);
      return {
        content: [{
          type: "text",
          text: `Error fetching calendar objects: ${JSON.stringify(error.message || error)}`
        }],
        isError: true
      };
    }
  }
);

server.tool(
  `get_my_${DAV_PROVIDER}_contact_lists`,
  {
    description: `Lists all of your contact address books from your ${DAV_PROVIDER} account. It returns a list of address book objects, each with details like its URL and name. Use this to find the \`addressBookUrl\` needed for fetching contacts.`,
    inputSchema: {}
  },
  async () => {
    if (!cardDavClient) return { content: [{ type: "text", text: "CardDAV client not initialized for this provider."}], isError: true };
    try {
      await cardDavClient.login();
      const addressBooks = await cardDavClient.fetchAddressBooks();
      return {
        content: [{
          type: "text",
          text: JSON.stringify(addressBooks, null, 2)
        }]
      };
    } catch (error) {
      console.error(`Error in get_my_${DAV_PROVIDER}_contact_lists:`, error);
      return {
        content: [{
          type: "text",
          text: `Error listing address books: ${JSON.stringify(error.message || error)}`
        }],
        isError: true
      };
    }
  }
);

server.tool(
  `get_contacts_from_${DAV_PROVIDER}_list`,
  {
    description: `Fetches all contacts from a specific address book. You must provide the \`addressBookUrl\` for the contact list you want to retrieve contacts from. You can get this URL from the \`get_my_${DAV_PROVIDER}_contact_lists\` tool. The contacts are returned in vCard format.`,
    inputSchema: {
      addressBookUrl: z.string().describe("The unique identifier (URL) of the contact list from which to fetch contacts. You can get this from 'get_my_contact_lists'."),
    },
  },
  async ({ addressBookUrl }) => {
    if (!cardDavClient) return { content: [{ type: "text", text: "CardDAV client not initialized for this provider."}], isError: true };
    try {
      await cardDavClient.login();
      const addressBooks = await cardDavClient.fetchAddressBooks(); // Needed to find the address book object
      const addressBook = addressBooks.find(ab => ab.url === addressBookUrl);

      if (!addressBook) {
        return {
          content: [{ type: "text", text: `Error: Address book with URL ${addressBookUrl} not found.` }],
          isError: true
        };
      }

      const vcards = await cardDavClient.fetchVCards({ addressBook });
      return {
        content: [{
          type: "text",
          text: JSON.stringify(vcards, null, 2)
        }]
      };
    } catch (error) {
      console.error(`Error in get_contacts_from_${DAV_PROVIDER}_list:`, error);
      return {
        content: [{
          type: "text",
          text: `Error fetching vCards: ${JSON.stringify(error.message || error)}`
        }],
        isError: true
      };
    }
  }
);

if (webDavClient) {
  server.tool(
    `list_my_files_and_folders_from_${DAV_PROVIDER}`,
    {
      description: `Lists files and folders from your ${DAV_PROVIDER} WebDAV storage. You can optionally provide a \`path\` to a specific folder. If no path is provided, it lists items from the root directory. This is only available for providers that support WebDAV.`,
      inputSchema: {
        path: z.string().optional().describe("The specific folder path to list. For example, 'Documents/Work'. If empty, lists files and folders in the main (root) directory."),
      },
    },
    async ({ path }) => {
      try {
        await webDavClient.login();
        let collectionUrl = webDavClient.serverUrl; // Base server URL from client
        if (path && path !== '/') {
          // Ensure no double slashes and correct joining
          const base = collectionUrl.endsWith('/') ? collectionUrl.slice(0, -1) : collectionUrl;
          const relativePath = path.startsWith('/') ? path.substring(1) : path;
          collectionUrl = `${base}/${relativePath}`;
        }

        const objects = await webDavClient.fetchObjects({ collection: collectionUrl });
        return {
          content: [{
            type: "text",
            text: JSON.stringify(objects, null, 2)
          }]
        };
      } catch (error) {
        console.error(`Error in list_my_files_and_folders_from_${DAV_PROVIDER}:`, error);
        return {
          content: [{
            type: "text",
            text: `Error listing WebDAV collection: ${JSON.stringify(error.message || error)}`
          }],
          isError: true
        };
      }
    }
  );

  server.tool(
    `get_file_or_folder_details_from_${DAV_PROVIDER}`,
    {
      description: `Retrieves detailed properties for a specific file or folder from your ${DAV_PROVIDER} WebDAV storage. You must provide the full \`fileUrl\` of the item, which you can get from \`list_my_files_and_folders_from_${DAV_PROVIDER}\`. This is only available for providers that support WebDAV.`,
      inputSchema: {
        fileUrl: z.string().describe("The unique identifier (URL) of the file or folder to get details for. You can get this from 'list_my_files_and_folders'."),
      },
    },
    async ({ fileUrl }) => {
      try {
        await webDavClient.login();
        // fetchObjects can be used with a full URL to an object to get its properties
        const objectProperties = await webDavClient.fetchObjects({ collection: fileUrl });
        return {
          content: [{
            type: "text",
            text: JSON.stringify(objectProperties, null, 2)
          }]
        };
      } catch (error) {
        console.error(`Error in get_file_or_folder_details_from_${DAV_PROVIDER}:`, error);
        return {
          content: [{
            type: "text",
            text: `Error getting WebDAV file metadata: ${JSON.stringify(error.message || error)}`
          }],
          isError: true
        };
      }
    }
  );
}

const transport = new StdioServerTransport();
server.connect(transport);
