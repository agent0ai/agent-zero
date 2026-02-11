# Usage Guide
This guide explores usage and configuration scenarios for Agent Zero. You can consider this as a reference post-installation guide.

![Utility Message with Solutions](../res/usage/first-task.png)

## Basic Operations
Agent Zero provides several basic operations through its interface:

### Restart Framework
The Restart button allows you to quickly restart the Agent Zero container without using the terminal:

![Restart Framework](../res/usage/restart.png)

- Click the "Restart" button in the sidebar dropdown
- A blue inline confirmation will appear indicating "Confirm"
- Once confirmed, the framework will reinitialize and restart the container

> [!TIP]
> Use the Restart function when you want to:
> - Reset the framework if you encounter unexpected behavior
> - See changes applied to the framework code

### Action Buttons
Located beneath the chat input box, Agent Zero provides a set of action buttons for enhanced control and visibility:

![Action Buttons](../res/usage/action-btns.png)
#### Chat Flow Control
- **Pause/Resume Agent:** Toggle button to pause and resume chat flow
  - Click to pause ongoing agent operations
  - Changes to "Resume Agent" when paused
  - Click again to resume chat flow and command execution

#### Knowledge and File Management
- **Import Knowledge:** Import external files into the agent's knowledge base
  - Supports `.txt`, `.pdf`, `.csv`, `.html`, `.json`, and `.md` formats
  - Files are stored in `/a0/knowledge/custom/main`
  - Success message confirms successful import
  - See [knowledge](../developer/architecture.md#knowledge) for more details

### File Browser: Manage files in the Agent Zero environment

![File Browser](../res/usage/file-browser.png)

- Upload new files and folders
- Download files (click filename) or folders (as zip archives)
- Rename and Delete files and folders
- Navigate directories using the "Up" button
- Edit files in the File Editor
- See [File Browser](#file-browser) section for detailed features

#### Debugging and Monitoring
- **Context:** View the complete context window sent to the LLM
  - Includes system prompts
  - Shows current conversation context
  - Displays active instructions and parameters

![Context](../res/usage/ui-context1.png)

### History:
Access the chat history in JSON format
- View the conversation as processed by the LLM
- Useful for debugging and understanding agent behavior
- Files are stored under `/a0/usr/chats/` inside the container

![History](../res/usage/ui-history1.png)

- **Nudge:** Restart the agent's last process
  - Useful when agents become unresponsive
  - Retries the last operation
  - Helps recover from stuck states

![Nudge](../res/usage/nudge.png)

> [!TIP]
> Use the Context and History buttons to understand how the agent interprets your instructions and debug any unexpected behavior.

### File Attachments
Agent Zero supports direct file attachments in the chat interface for seamless file operations:

#### Attaching Files
- Click the attachment icon (📎) on the left side of the chat input box
- Select one or multiple files to attach
- Preview attached files before sending:
  - File names are displayed with their types (HTML, PDF, JPG, etc.)
  - Images show thumbnails when available
  - Files are listed in the chat input area waiting to be sent

![File Attachments](../res/usage/attachments-1.png)

#### Working with Attached Files
- Files can be referenced directly in your messages
- Agent Zero can:
  - Process attached files
  - Move files to specific directories
  - Perform operations on multiple files simultaneously
  - Confirm successful file operations with detailed responses

![Working with Attachments](../res/usage/attachments-2.png)

> [!TIP]
> When working with multiple files, you can attach them all at once and then give instructions about what to do with them. The agent will handle them as a batch while keeping you informed of the progress.

## Tool Usage
Agent Zero's power comes from its ability to use [tools](../developer/architecture.md#tools). Here's how to leverage them effectively:

- **Understand Tools:** Agent Zero includes default tools like knowledge (powered by SearXNG), code execution, and communication. Understand the capabilities of these tools and how to invoke them.

### Browser Agent Status & MCP Alternatives
The built-in browser agent currently has dependency issues on some systems. If web automation is critical, prefer MCP-based browser tools instead:

- **Browser OS MCP**
- **Chrome DevTools MCP**
- **Playwright MCP**

See [MCP Setup](mcp-setup.md) for configuration guidance and recommended servers.

### Agent-to-Agent (A2A) Communication

Agent Zero instances can communicate with each other using the A2A protocol. This enables:

- **Task delegation** to specialized agent instances
- **Distributed workflows** across multiple agents
- **Project-specific collaboration** with isolated contexts

To enable A2A connectivity, go to **Settings → MCP/A2A → A2A Server** and toggle the server on. You'll receive a connection URL that other Agent Zero instances can use to communicate with your agent.

See [A2A Setup](a2a-setup.md) for detailed configuration and use cases.

## Example of Tools Usage: Web Search and Code Execution
Let's say you want Agent Zero to perform some financial analysis tasks. Here's a possible prompt:

> Please be a professional financial analyst. Find last month Bitcoin/ USD price trend and make a chart in your environment. The chart must have highlighted key points corresponding with dates of major news about cryptocurrency. Use the `search_engine` and `document_query` tools to find the price and the news, and the `code_execution_tool` to perform the rest of the job.

Agent Zero might then:

1. Use the `search_engine` and `document_query` tools to query a reliable source for the Bitcoin price and for the news about cryptocurrency as prompted.
2. Extract the price from the search results and save the news, extracting their dates and possible impact on the price.
3. Use the `code_execution_tool` to execute a Python script that performs the graph creation and key points highlighting, using the extracted data and the news dates as inputs.
4. Save the final chart on disk inside the container and provide a link to it with the `response_tool`.

> [!NOTE]
> The first run of `code_execution_tool` may take a while as it downloads and builds the Agent Zero Docker image. Subsequent runs will be faster.

This example demonstrates how to combine multiple tools to achieve an analysis task. By mastering prompt engineering and tool usage, you can unlock the full potential of Agent Zero to solve complex problems.

## Multi-Agent Cooperation
One of Agent Zero's unique features is multi-agent cooperation.

- **Creating Sub-Agents:** Agents can create sub-agents to delegate sub-tasks.  This helps manage complexity and distribute workload.
- **Communication:** Agents can communicate with each other, sharing information and coordinating actions. The system prompt and message history play a key role in guiding this communication.
- **Hierarchy:** Agent Zero uses a [hierarchical structure](../developer/architecture.md#agent-hierarchy-and-communication), with superior agents delegating tasks to subordinates.  This allows for structured problem-solving and efficient resource allocation.

![](../res/usage/multi-agent.png)

## Projects
Projects are isolated workspaces that provide dedicated context, instructions, memory, and secrets for specific tasks or clients. They are one of Agent Zero's most powerful organizational features, preventing context bleed and enabling focused, specialized agent behavior.

### What Projects Provide

Each project includes:

- **Isolated workspace** under `/a0/usr/projects/<project_name>/`
- **Custom instructions** automatically injected into system prompts
- **Dedicated or shared memory** to control context isolation
- **Project-scoped secrets and variables** for secure credential management
- **Git repository integration** for cloning and working with codebases
- **File structure injection** for automatic codebase awareness
- **Custom agent configurations** including subagent settings
- **Knowledge base integration** with project-specific documents

### Creating Projects

There are two ways to access project management:

1. **Dashboard Access**: Click **Projects** in the sidebar to open the Projects modal
2. **Quick Access**: Click the project dropdown in the top-right corner (shows "No project" when none is active)

![Project Creation](../res/usage/projects/projects-creation.png)

#### Empty Projects

Create a new empty project workspace:
1. Click **"Create project"**
2. Enter a **title** (human-readable name)
3. Choose a **color tag** for visual identification
4. Click **"Create and continue"**

#### Git-Based Projects

Clone a repository directly into your project workspace:
1. Enter a **Git repository URL** (public or private)
2. Optionally provide an authentication token for private repos
3. Agent Zero clones the repository and sets up the project structure

![Git Clone Progress](../res/usage/projects/projects-gitprojects-clone.png)

The system clones the `main` branch by default. You can ask the agent to checkout other branches later. After cloning, you'll see repository status including current branch, clean/dirty state, and last commit info.

![Git Project Status](../res/usage/projects/projects-git-projects-tree.png)

> [!NOTE]
> If the cloned repository already contains a `.a0proj/` configuration folder, Agent Zero merges the existing configuration with your specified preferences.

### Project Configuration

![Project Configuration](../res/usage/projects/projects-desc-and-instructions.png)

#### Description and Instructions

- **Description**: Helps you and the agent understand the project's purpose and context
- **Instructions**: Critical field that gets injected into the agent's system prompt when the project is active

> [!IMPORTANT]
> Well-written instructions are key to effective project-specific behavior. Be specific about:
> - The agent's role and expertise for this project
> - Directory paths and file locations
> - Expected workflows and procedures
> - Quality standards and validation rules
> - Output formats and requirements

**Example instructions:**

```markdown
## Your Role
You are an expert Financial Data Analyst working with Excel automation.

## Operational Context
- Work directory: `/usr/projects/excel-finance/`
- Input data: `/usr/projects/excel-finance/data/incoming/`
- Reports output: `/usr/projects/excel-finance/reports/`

## Core Responsibilities
1. Scan for new Excel/CSV files in incoming directory
2. Validate and clean data (check for missing values, duplicates)
3. Consolidate data from multiple sources
4. Generate executive reports with visualizations
5. Flag compliance issues and anomalies
```

#### Memory Isolation

Choose how project memory is managed:

- **Own memory** (recommended): Project has isolated memory under `vector_db/projects/<project_name>/`
  - Prevents context bleed between projects
  - Ideal for client work, sensitive projects, or distinct domains
  
- **Global memory**: Project shares the default memory pool
  - Useful when projects need shared knowledge
  - Better for closely related projects

#### Variables and Secrets

Projects support scoped configuration:

- **Variables** (non-sensitive): Stored in `.a0proj/variables.env`

  ```bash
  API_BASE_URL=https://api.example.com
  OUTPUT_FORMAT=json
  ```

- **Secrets** (sensitive): Stored in `.a0proj/secrets.env`

  ```bash
  API_KEY=sk-abc123xyz...
  DATABASE_PASSWORD=super_secret_pwd
  ```

Reference these in your prompts: "Use my `API_KEY` to authenticate with the service"

> [!WARNING]
> Secrets may not be included in backup archives. Keep a separate manual copy of critical credentials.

#### File Structure Injection

Projects can automatically inject their directory structure into the agent's context. This is configurable per project:

- **Max depth**: Directory levels to scan (default: 5)
- **Max files/folders**: Limits for context size
- **Gitignore patterns**: Filter out build artifacts, dependencies, etc.

The default ignores: `.a0proj/`, `venv/`, `__pycache__/`, `node_modules/`, `.git/`

This feature helps the agent understand your codebase structure without manual explanation.

### Activating Projects

To use a project, activate it for your current chat:

1. Click the project dropdown in the top-right corner
2. Select the desired project from the list
3. The project activates immediately

![Project Activation](../res/usage/projects/projects-activate-project.png)

Each chat can have its own active project. Multiple chats can use different projects simultaneously.

Once activated, the agent:
- Follows project-specific instructions
- Uses project memory (if isolated)
- Has access to project secrets and variables
- Sees the project file structure (if enabled)
- Works in the project directory by default

![First Operations](../res/usage/projects/projects-first-ops.png)

### Project Directory Structure

```
/a0/usr/projects/<project_name>/
├── .a0proj/                    # Project metadata (managed by the application)
│   ├── project.json            # Main configuration
│   ├── variables.env           # Non-sensitive config
│   ├── secrets.env             # Sensitive credentials
│   ├── agents.json             # Subagent settings
│   ├── instructions/           # Additional instruction files
│   └── knowledge/              # Project knowledge base
├── src/                        # Your actual project files
├── data/                       # Data files
└── ...                         # Other project content
```

### Common Use Cases

**Multi-Client Work**: Create separate projects for each client with isolated memory and credentials

**Multi-Language Development**: Organize by tech stack (Python ML, Node.js webapp, Go microservices)

**Domain-Specific Tasks**: Separate projects for finance, marketing, HR with domain-specific instructions

**Automated Workflows**: Combine with [Tasks & Scheduling](#tasks--scheduling) for recurring project-based work

### Best Practices

- Use **own memory** by default for client work to prevent context bleed
- Write **specific instructions** - mention paths, formats, and quality standards
- Choose **distinct colors** for easy visual identification when switching
- Keep **secrets separate** from version control - backup manually
- **Adjust file structure limits** based on project size
- **Clean memory periodically** via Memory Dashboard for optimal performance

> [!TIP]
> For a comprehensive guide to creating and managing projects, including detailed examples and troubleshooting, see the [Projects Tutorial](projects.md).

See also:
- [Projects in Extensions](../developer/extensions.md#projects) - Technical structure details
- [Tasks & Scheduling](#tasks--scheduling) - Automate project-based work
- [Memory Management](#memory-management) - Maintain project knowledge

## Tasks & Scheduling
Tasks enable Agent Zero to run automated or scheduled work in isolated contexts. They're perfect for recurring workflows, batch processing, or time-delayed operations that don't require immediate attention.

### What Are Tasks?

Tasks are autonomous work units that Agent Zero executes in dedicated or shared chat contexts. Each task includes:

- **Prompt and Instructions**: What the agent should do
- **Execution Schedule**: When to run (cron schedule, specific times, or manual)
- **Project Association**: Optional project context with its instructions and secrets
- **Dedicated Context**: Each task can maintain its own conversation history
- **State Management**: Tracks idle, running, disabled, or error states
- **Result Tracking**: Stores last run time and execution results

### Task Types

Agent Zero supports three types of tasks:

#### Scheduled Tasks
Run on a recurring schedule using cron syntax:
- **Daily reports**: `0 9 * * *` (every day at 9 AM)
- **Hourly checks**: `0 * * * *` (every hour)
- **Weekly summaries**: `0 9 * * 1` (Mondays at 9 AM)
- **Custom intervals**: Full cron flexibility for complex schedules

#### Planned Tasks
Execute at specific, predetermined times:
- **One-time future execution**: Single date/time
- **Multi-step campaigns**: List of specific execution times
- **Event-driven sequences**: Coordinate with external schedules

#### Ad-hoc Tasks
Manual execution for on-demand work:
- **Quick batch jobs**: Run when needed
- **Testing workflows**: Verify task configuration
- **One-off operations**: Tasks that don't need scheduling

### Creating Tasks

#### From the UI

Access the Task Scheduler from the sidebar:

1. Click **Settings** → **Tasks Scheduler**
2. Click **"New Task"** to create a task

![Task Scheduler](../res/usage/tasks/scheduler-1.png)

The scheduler shows:
- **Task List**: All configured tasks with their state
- **Filter Controls**: By type (scheduled, planned, ad-hoc) and state
- **Quick Actions**: Run, pause, edit, or delete tasks
- **Task Details**: Name, project association, last run, next run time

#### From Chat

Ask the agent to create tasks programmatically:

```
Create a scheduled task that checks my email inbox every morning at 8 AM 
and summarizes new messages from the last 24 hours.
```

The agent uses the `scheduler` tool to create tasks based on your natural language description.

### Task Configuration

![Edit Task](../res/usage/tasks/edit-task.png)

When editing a task, you configure:

#### Task Name
A unique identifier for the task:
- Use descriptive names: "Morning report for incoming Gmail"
- Keep it concise but clear
- Helps identify tasks in logs and notifications

#### Task Type
Choose the execution model:
- **Scheduled**: Recurring cron-based execution
- **Planned**: Specific date/time list
- **Ad-hoc**: Manual execution only

> [!NOTE]
> Task type cannot be changed after creation. To switch types, create a new task.

#### Project Association
Optionally link the task to a project:

**Benefits of project-scoped tasks:**
- Task inherits project instructions automatically
- Access to project-specific secrets and variables
- Uses project's isolated memory (if configured)
- Runs in project's working directory
- Perfect for client-specific or domain-specific automation

**Example:**
- Project: "Financial Reports"
- Task: "Daily Portfolio Summary"
- Result: Task automatically uses financial analysis instructions, API keys, and memory from the project

#### State Management
Control task execution:

- **Idle**: Ready to run when scheduled (green indicator)
- **Running**: Currently executing (blue indicator)
- **Disabled**: Won't execute even if scheduled (gray indicator)
- **Error**: Last execution failed (red indicator)

Toggle state to temporarily disable tasks without deleting them.

#### Execution Plan
For **Scheduled Tasks**, configure the cron schedule:

**Common patterns:**

```
# Every day at 9 AM
0 9 * * *

# Every hour
0 * * * *

# Every Monday at 10 AM
0 10 * * 1

# Every 15 minutes
*/15 * * * *

# First day of month at midnight
0 0 1 * *
```

**Timezone aware**: Tasks respect your configured timezone setting

For **Planned Tasks**, add specific execution times:
- Click "Add Execution Time"
- Pick date and time
- Tasks execute in order
- Completed executions move to "Done" list

### Task Execution

#### Dedicated vs. Shared Context

**Dedicated Context** (recommended):
- Each task has its own isolated chat history
- Prevents context pollution between tasks
- Better for independent, recurring workflows
- Default for UI-created tasks

**Shared Context**:
- Task shares a chat context (useful for agent-created tasks)
- Can build on previous task executions
- Useful for sequential, related operations

#### Execution Flow

When a task runs:

1. **Context Preparation**
   - Creates or loads the task's chat context
   - Activates associated project (if configured)
   - Loads project instructions, secrets, and memory

2. **Prompt Injection**
   - Injects system prompt (if specified)
   - Adds task-specific instructions
   - Includes any file attachments

3. **Agent Execution**
   - Agent receives the prompt as a user message
   - Executes using available tools
   - Can use project-scoped resources

4. **Result Handling**
   - Stores execution result and timestamp
   - Updates task state (idle or error)
   - Sends notifications (if configured)
   - For Planned Tasks: moves execution to "Done" list

#### Monitoring Execution

**Real-time monitoring:**
- Running tasks show "Running" state in scheduler
- View task's chat context to see agent progress
- Stop tasks mid-execution if needed

**Execution history:**
- **Last Run**: Timestamp of most recent execution
- **Next Run**: Scheduled time for next execution
- **Last Result**: Output or error from last run

### Common Use Cases

#### Daily Reports

```
Task: "Morning Inbox Summary"
Type: Scheduled (0 9 * * *)
Project: "Email Automation"
Prompt: "Check my Gmail inbox for new messages from the last 24 hours.
Summarize important emails by category and highlight any urgent items."
```

#### Recurring Monitoring

```
Task: "Server Health Check"
Type: Scheduled (*/30 * * * *)
Project: "DevOps Monitoring"
Prompt: "Check server status, CPU usage, and disk space.
Alert me if any metric exceeds threshold."
```

#### Batch Processing

```
Task: "Weekly Data Export"
Type: Scheduled (0 2 * * 0)
Project: "Analytics"
Prompt: "Export last week's analytics data to CSV.
Upload to cloud storage and send summary report."
```

#### Campaign Automation

```
Task: "Product Launch Sequence"
Type: Planned
Executions:
  - 2026-03-01 09:00 - Send launch announcement
  - 2026-03-03 14:00 - Send feature highlights
  - 2026-03-07 10:00 - Send customer testimonials
Project: "Marketing Campaigns"
```

### Integration with Projects

Tasks and Projects are designed to work together:

**Pattern: Project-Scoped Automation**

1. Create a project with domain-specific instructions

   ```
   Project: "Customer Support"
   Instructions: "You are a customer support analyst.
   Monitor ticket queue, categorize by urgency, draft responses."
   ```

2. Create a recurring task for that project

   ```
   Task: "Ticket Queue Monitor"
   Schedule: Every 2 hours
   Project: "Customer Support"
   Prompt: "Check new tickets and categorize them."
   ```

3. Task automatically uses:
   - Project instructions (support analyst role)
   - Project secrets (support system API keys)
   - Project memory (previous ticket patterns)
   - Project file structure (template responses)

**Benefits:**
- Consistent behavior across task executions
- No need to repeat instructions in each task
- Easy to update behavior (edit project instructions once)
- Clean separation of concerns (project = context, task = action)

### Notifications

Tasks can trigger notifications on completion or failure:

- Configure notification preferences in Settings
- Set up notification channels (email, Slack, webhook)
- Tasks automatically send status updates
- Critical for unattended automation

See [Notifications](../developer/notifications.md) for configuration details.

### Multi-Source Aggregation
Tasks can pull from multiple sources:

```
"Aggregate data from:
1. Sales CRM API
2. Marketing analytics dashboard
3. Customer support tickets
Generate unified weekly report."
```

> [!TIP]
> Combine **Projects + Tasks + Notifications** for powerful automation workflows. Example: Create a "Client Reports" project with instructions, then add scheduled tasks for each client that inherit those instructions automatically.

### Next Steps

Explore related features:

- [Projects](#projects) - Create isolated contexts for tasks
- [Notifications](../developer/notifications.md) - Understand the notification system
- [Memory Management](#memory-management) - Understand task memory isolation
- [Secrets & Variables](#secrets--variables) - Secure credentials for tasks

## Secrets & Variables
Use the Settings → **Secrets** and **Variables** fields to store credentials and non-sensitive configuration values.

- **Secrets** (sensitive): API keys, passwords, tokens
- **Variables** (non-sensitive): URLs, usernames, flags

You can reference these values in prompts by name. For example, store `MY_GMAIL` as a secret and instruct the agent to use it when prompted.

> [!IMPORTANT]
> Secrets are stored in `/a0/usr/secrets.env`.

> [!NOTE]
> Project-scoped secrets and variables (when using Projects) live under `/a0/usr/projects/<project_name>/.a0proj/` (`secrets.env`, `variables.env`).

## Remote Access via Tunneling

Agent Zero includes a secure tunneling feature that allows you to expose your local instance to the internet. This makes it possible to access your Agent Zero instance from anywhere or share it with others without complex network configuration.

### How Tunneling Works

Agent Zero uses the [Flaredantic](https://pypi.org/project/flaredantic/) library to create secure tunnels. These tunnels:

- Are secure (HTTPS)
- Don't require any configuration
- Generate unique URLs for each session
- Can be regenerated on demand

### Creating a Tunnel

1. Open **Settings** in the sidebar
2. Navigate to the **External Services** tab
3. Click on **Flare Tunnel** in the navigation menu
4. Click the **Create Tunnel** button to generate a new tunnel
5. Once created, the tunnel URL will be displayed and can be copied to share with others
6. The tunnel URL remains active until you stop the tunnel or close Agent Zero

### Security Considerations

When sharing your Agent Zero instance via a tunnel:

- Anyone with the URL can access your Agent Zero instance
- No additional authentication is added beyond what your Agent Zero instance already has
- **Always set up authentication before creating a tunnel** (see below)
- The tunnel exposes only your Agent Zero instance, not your entire system

> [!IMPORTANT]
> When attempting to create a tunnel without authentication configured, Agent Zero will display a security warning.

### Adding Authentication for Tunnels

To secure your tunneled Agent Zero instance, configure authentication in Settings:

1. Open **Settings** in the Agent Zero UI
2. Navigate to the **Authentication** section
3. Enter your desired username in the **UI Login** field
4. Enter a strong password in the **UI Password** field
5. Click **Save** to apply the changes

Alternatively, you can set environment variables:

```bash
AUTH_LOGIN=your_username
AUTH_PASSWORD=your_password
```

This will require users to enter these credentials when accessing your tunneled Agent Zero instance.

### Troubleshooting Tunnels

If you encounter issues with the tunnel feature:

1. Check your internet connection
2. Try regenerating the tunnel URL
3. Restart Agent Zero
4. Check the console logs for any error messages

> [!TIP]
> Combine tunneling with authentication for secure remote access to your Agent Zero instance from any device, including mobile phones and tablets.

## Voice Interface
Agent Zero provides both Text-to-Speech (TTS) and Speech-to-Text (STT) capabilities for natural voice interaction:

### Text-to-Speech
Enable voice responses from agents:
- Toggle the "Speech" switch in the Preferences section of the sidebar
- Agents will use your system's built-in voice synthesizer to speak their messages
- Click the "Stop Speech" button above the input area to immediately stop any ongoing speech
- You can also click the speech button when hovering over messages to speak individual messages or their parts

![TTS Stop Speech](../res/usage/ui-tts-stop-speech1.png)

- The interface allows users to stop speech at any time if a response is too lengthy or if they wish to intervene during the conversation.

The TTS uses a standard voice interface provided by modern browsers, which may sound robotic but is effective and does not require complex AI models. This ensures low latency and quick responses across various platforms, including mobile devices.

> [!TIP]
> The Text-to-Speech feature is great for:
> - Multitasking while receiving agent responses
> - Accessibility purposes
> - Creating a more interactive experience

### Speech-to-Text
Send voice messages to agents using OpenAI's Whisper model (does not require OpenAI API key!):

1. Click the microphone button in the input area to start recording
2. The button color indicates the current status:
   - Grey: Inactive
   - Red: Listening
   - Green: Recording
   - Teal: Waiting
   - Cyan (pulsing): Processing

Users can adjust settings such as silence threshold and message duration before sending to optimize their interaction experience.

Configure STT settings in the Settings page:
- **Model Size:** Choose between Base (74M, English) or other models
  - Note: Only Large and Turbo models support multiple languages
- **Language Code:** Set your preferred language (e.g., 'en', 'fr', 'it', 'cz')
- **Silence Detection:**
  - Threshold: Adjust sensitivity (lower values are more sensitive)
  - Duration: Set how long silence should last before ending recording
  - Timeout: Set maximum waiting time before closing the microphone

![Speech to Text Settings](../res/usage/ui-settings-5-speech-to-text.png)

> [!IMPORTANT]
> All STT and TTS functionalities operate locally within the Docker container,
> ensuring that no data is transmitted to external servers or OpenAI APIs. This
> enhances user privacy while maintaining functionality.

## Mathematical Expressions
- **Complex Mathematics:** Supports full KaTeX syntax for:
  - Fractions, exponents, and roots
  - Matrices and arrays
  - Greek letters and mathematical symbols
  - Integrals, summations, and limits
  - Mathematical alignments and equations

![KaTeX display](../res/usage/ui-katex-2.png)

> [!TIP]
> When asking the agent to solve mathematical problems, it will automatically respond using KaTeX formatting for clear and professional-looking mathematical expressions.

### File Browser
Agent Zero provides a powerful file browser interface for managing your workspace:

#### Interface Overview
- **Navigation Bar**: Shows current directory path with "Up" button for parent directory
- **File List**: Displays files and directories with key information:
  - Name (sortable)
  - Size in bytes
  - Last modified timestamp
- **Action Icons**: Each file/directory has:
  - menu for edit and rename actions
  - Download button
  - Delete button (with confirmation)

![File Browser](../res/usage/ui-file-browser.png)

#### Features
- **Directory Navigation**:
  - Click directories to enter them
  - Use "Up" button to move to parent directory
  - Current path always visible for context

> [!NOTE]
> The file browser lets you navigate the Agent Zero filesystem. For file-based work, keep your working files in `/a0/usr` (or inside a Project workspace).
>
- **File Operations**:
  - Create new files and directories
  - Delete existing files and directories
  - Download files to your local system
  - Upload files from your local system
- **File Information**:
  - Visual indicators for file types (folders, code files, documents)
  - Size information in human-readable format
  - Last modification timestamps
- **Bulk Operations**:
  - Upload multiple files simultaneously
- **File and Directory Editing**:
  - Limited to 100MB files
  - Binary files cannot be edited

> [!TIP]
> The File Browser integrates seamlessly with Agent Zero's capabilities. You can reference files directly in your conversations, and the agent can help you manage, modify, and organize your files.

## Memory Management
Agent Zero includes a sophisticated memory management system that stores and retrieves information from conversations, knowledge sources, and learning experiences. The Memory Dashboard provides a powerful interface to view, search, filter, edit, and delete memory entries stored in the vector database.

### Accessing the Memory Dashboard
Open the Memory Dashboard from the sidebar to manage your agent's memory:

1. Click the **Memory** button in the sidebar
2. The dashboard displays all memory entries with their metadata and preview
3. Memory entries are organized by directory (e.g., "default") and area (e.g., "All Areas", "main")

![Memory Dashboard](../res/usage/memory-dashboard.png)

### Dashboard Features

#### Filtering and Organization
The dashboard provides several ways to organize and filter memory entries:

- **Memory Directory**: Select which memory directory to view (default or project-specific)
- **Area Filter**: Filter memories by area to focus on specific contexts
- **Limit Control**: Adjust the number of results displayed (default: 1000)
- **Statistics Bar**: View counts at a glance:
  - Total: All memory entries in the directory
  - Filtered: Entries matching current filters
  - Knowledge: Entries from knowledge sources
  - Conversation: Entries from chat interactions

#### Search Functionality
Find specific memories using the powerful search feature:

- **Search Bar**: Enter keywords to search memory content
- **Threshold Slider**: Adjust search sensitivity (0.00 - 1.00)
  - Lower values return more results with looser matching
  - Higher values return fewer, more precise matches
  - Default threshold: 0.60
- **Real-time Search**: Results update as you type

> [!TIP]
> Use the threshold slider to balance between broad discovery (lower values) and precise matching (higher values). Start with 0.60 and adjust based on your results.

#### Memory Entry Information
Each memory entry displays key information:

- **Tags**: Visual indicators showing the memory type (MAIN, Knowledge, etc.)
- **Timestamp**: When the memory was created (format: MM/DD HH:MM)
- **Preview**: First few lines of the memory content
- **Action Icons**: Quick access to view details, edit, or delete

### Viewing and Editing Memories
Click any memory entry to open the detailed view with full editing capabilities:

![Memory Details](../res/usage/memory-editing.png)

#### Memory Details View
The details panel provides comprehensive information about each memory:

- **Memory Content**: Full text of the stored memory
  - Syntax highlighting for structured content
  - Editable text area for modifications
- **Metadata Panel**: Complete memory information
  - Unique ID
  - Area classification
  - Source type (e.g., "Knowledge")
  - Timestamp (creation date and time)
  - Source file (if applicable)

#### Editing Memories
Modify memory entries directly from the details view:

1. Click on any memory entry to open the details panel
2. Edit the memory content in the text area
3. Click the **Save** button (checkmark icon) to apply changes
4. Click the **Cancel** button (X icon) to discard changes

> [!NOTE]
> Edited memories are immediately updated in the vector database and will affect how the agent recalls and uses this information in future interactions.

#### Deleting Memories
Remove unwanted or outdated memory entries:

1. Open the memory details view
2. Click the **Delete** button (trash icon) in the action bar
3. Confirm the deletion when prompted
4. The memory is permanently removed from the vector database

Alternatively, delete directly from the main dashboard:
- Click the delete icon on any memory entry in the list
- Confirm the deletion

> [!WARNING]
> Deleted memories cannot be recovered. Use caution when removing entries, especially those from knowledge sources or important conversations.

#### Clearing Memories
For bulk cleanup operations:

- Click the **Clear** button in the dashboard header to remove all filtered memories
- This is useful when you need to reset a specific area or start fresh with a memory directory
- Always review your filters before clearing to avoid unintended deletions

### Memory Types and Sources

#### Knowledge Memories
Memories derived from uploaded knowledge files:
- Marked with "Knowledge" tag
- Include source file information
- Created when importing documents via Import Knowledge button
- Stored persistently unless manually deleted

#### Conversation Memories
Memories from chat interactions:
- Marked with conversation indicators
- Created automatically as the agent learns from interactions
- Include contextual information about when and why they were created
- Help the agent maintain continuity across sessions

### Best Practices with Memory

#### Regular Maintenance
- **Review Periodically**: Check your memory entries monthly to remove outdated information
- **Organize by Area**: Use areas to categorize memories by project or topic
- **Clean Up Test Data**: Remove experimental or test memories that aren't needed
- **Monitor Growth**: Keep an eye on total memory count to maintain performance

#### Search Optimization
- **Use Specific Keywords**: More specific terms yield better results
- **Adjust Threshold**: Fine-tune the threshold based on your needs
- **Filter First**: Use area and directory filters before searching for better results
- **Iterate Searches**: Try different search terms if initial results aren't helpful

#### Content Quality
- **Keep Relevant**: Remove memories that are no longer useful or accurate
- **Update Information**: Edit memories when information becomes outdated
- **Add Context**: When editing, ensure memories remain clear and useful
- **Avoid Duplicates**: Remove redundant memories that store the same information

#### Project Integration
When using Projects (see [Projects](#projects)):
- Each project maintains its own memory directory
- Memories are isolated between projects to prevent context bleed
- Use project-specific memory directories for focused work
- Clear project memories when archiving completed projects

> [!TIP]
> Combine memory management with the backup system to preserve important memory states. Before clearing or making bulk changes, create a backup so you can restore if needed.

> [!IMPORTANT]
> Memory management directly affects agent behavior and recall. Regularly maintaining your memory database ensures optimal agent performance and relevant context retention.

## Backup & Restore
Agent Zero provides a comprehensive backup and restore system to protect your data and configurations. This feature helps you safeguard your work and migrate Agent Zero setups between different systems.

### Creating Backups
Access the backup functionality through the Settings interface:

1. Click the **Settings** button in the sidebar
2. Navigate to the **Backup & Restore** tab
3. Click **Create Backup** to start the backup process

#### What Gets Backed Up
By default, Agent Zero backs up your most important data:

- **Knowledge Base**: Your custom knowledge files and documents
- **Memory System**: Agent memories and learned information
- **Chat History**: All your conversations and interactions
- **Configuration Files**: Settings, API keys, and system preferences
- **Custom Skills**: Any skills you've added or modified (SKILL.md format)
- **Uploaded Files**: Documents and files you've worked with

> [!NOTE]
> Chat history is stored at `/a0/usr/chats/` inside the container.

#### Customizing Backup Content
Before creating a backup, you can customize what to include:

- **Edit Patterns**: Use the built-in editor to specify exactly which files and folders to backup
- **Include Hidden Files**: Choose whether to include system and configuration files
- **Preview Files**: See exactly what will be included before creating the backup
- **Organized View**: Files are grouped by directory for easy review

> [!TIP]
> The backup system uses pattern matching, so you can include or exclude specific file types. For example, you can backup all `.py` files but exclude temporary `.tmp` files.

#### Creating Your Backup
1. Review the file preview to ensure you're backing up what you need
2. Give your backup a descriptive name
3. Click **Create Backup** to generate the archive
4. The backup file will download automatically as a ZIP archive

> [!NOTE]
> Backup creation may take a few minutes depending on the amount of data. You'll see progress updates during the process.
> Secrets stored in `/a0/usr/secrets.env` are not always included in backup archives. Keep a manual copy if you rely on secrets.

### Restoring from Backup
The restore process allows you to recover your Agent Zero setup from a previous backup:

#### Starting a Restore
1. Navigate to **Settings** → **Backup & Restore** tab
2. Click **Restore from Backup**
3. Upload your backup ZIP file

#### Reviewing Before Restore
After uploading, you can review and customize the restore:

- **Inspect Metadata**: View information about when and where the backup was created
- **Edit Restore Patterns**: Choose exactly which files to restore
- **Preview Changes**: See which files will be restored, overwritten, or skipped
- **Cross-System Compatibility**: Paths are automatically adjusted when restoring on different systems

#### Restore Options
Configure how the restore should handle existing files:

- **Overwrite**: Replace existing files with backup versions
- **Skip**: Keep existing files, only restore missing ones
- **Backup Existing**: Create backup copies of existing files before overwriting

#### Clean Before Restore
Optionally clean up existing files before restoring:

- **Smart Cleanup**: Remove files that match backup patterns before restoring
- **Preview Cleanup**: See which files would be deleted before confirming
- **Safe Operation**: Only affects files that match your specified patterns

### Best Practices

#### When to Create Backups
- **Before Major Changes**: Always backup before significant modifications
- **Regular Schedule**: Create weekly or monthly backups of your work
- **Before System Updates**: Backup before updating Agent Zero or system components
- **Project Milestones**: Save backups when completing important work

#### Backup Management
- **Descriptive Names**: Use clear names like "project-completion-2024-01"
- **External Storage**: Keep backup files in a safe location outside Agent Zero
- **Multiple Versions**: Maintain several backup versions for different time periods
- **Test Restores**: Occasionally test restoring backups to ensure they work

#### Security Considerations
- **Secrets**: Backups do **not** reliably include `/a0/usr/secrets.env`. Copy it manually when migrating.
- **Secure Storage**: Store backup files securely and don't share them
- **Clean Systems**: When restoring on new systems, verify all configurations

### Common Use Cases

#### System Migration
Moving Agent Zero to a new server or computer:
1. Create a complete backup on the original system
2. Install Agent Zero on the new system
3. Restore the backup to migrate all your data and settings

#### Project Archival
Preserving completed projects:
1. Create project-specific backup patterns
2. Include only relevant files and conversations
3. Store the backup as a project archive

#### Development Snapshots
Saving work-in-progress states:
1. Create frequent backups during development
2. Use descriptive names to track progress
3. Restore previous versions if something goes wrong

#### Team Collaboration
Sharing Agent Zero configurations:
1. Create backups with shared configurations and tools
2. Team members can restore to get consistent setups
3. Include documentation and project files

> [!IMPORTANT]
> Always test your backup and restore process in a safe environment before relying on it for critical data. Keep multiple backup versions and store them in secure, accessible locations.

> [!TIP]
> The backup system is designed to work across different operating systems and Agent Zero installations. Your backups from a Windows system will work on Linux, and vice versa.
