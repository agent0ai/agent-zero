# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Mcp setup documentation
- Contextual reminder for mcps with multi-step-processes for agent to not get distracted, to continue process.
- Mcp setup documentation
- Contextual reminder for mcps with multi-step-processes for agent to not get distracted, to continue process.

### Bug Fixes

- SVG optimization
- Status-icon
- Bigger modals
- File browser deletion bug + parent directory
- Toast handling, mobile breakpoint
- Make browser agent compatible with PlayWright 1.50 (#381)
- Google embedding api key param (#369)
- Synchronize job loop with development instance
- Startup error missing module
- Mcp tool call error because of erroneous await()
- Mcp server tool discovery
- Add missing error handling (#405)
- Use async versions of faiss methods in memory helper (#406)
- Import sentence_transfomers on pure cpu was failing (#429)
- Startup error missing module
- Mcp tool call error because of erroneous await()
- Mcp server tool discovery
- Mcp get_tools_prompt fix for tools with optional arguments
- Python.lang.security.audit.eval-detected.eval-detected-python-helpers-memory.py (#444)
- Deps for document_query, formatting of knowledge_tool results
- Typo in prompt
- More spcific thought headlines
- Response tool examples were wrong for researcher and developer agents (#607)
- Do not crash if runtime parameter is not set in code exec (#641)
- Token auth and reconfiguration
- Change a2a context type to BACKGROUND
- Make a2a chats temporary
- Notification fixes, refactor and restart toast persistence
- Scroll-fightig free message scrolling
- Code-exe autoscroll
- Scrolling of content in code-exe should honor global autoscroll
- Reenable autoscroll when history hits bottom
- Timezone switching spam bug (#664)
- *(browser)* Enforce correct viewport aspect ratio for browser agent
- Review refinements
- Eview refinements for memory dashboard
- Chat list fit-content/grow
- Chat list fit-content/grow
- Sidebar, welcome screen and UX
- Respect for task-only contexts
- Validate existing agent for context
- Check if project exists when activating
- Improve error handling for project activation in existing context
- Scheduler polling unchanged task list
- Edit task with project
- Dropdown behind sidebar-bottom
- Take durationms from backend
- Backend not setting agent no; agent no in responses
- Browser screenshot flashing
- Browser holding timestamp
- Skip root pwd change in non-docker env
- Update upload path from tmp/uploads to usr/uploads
- Skip empty AI messages in output_langchain to prevent API rejection
- Move default files; harden framework api/prompt
- Add host networking to the buildx builder for reliable package downloads and update setup documentation.
- Pin Kali mirror in Dockerfile for reliable builds and update dev setup documentation with expanded troubleshooting for build issues.
- Change Kali mirror URL from HTTPS to HTTP to avoid TLS verification issues in the base image.
- Resolve LiteLLM proxy routing and OMP crash on macOS
- Correct env var priority over YAML defaults for api_base resolution

### Bugfix

- Json lead disabled

### CI/CD

- Add emoji names, concurrency groups, timeouts, and uv caching to workflows
- Add paths-ignore, dependency review, and CodeQL security scanning
- Add issue templates, PR template, and Dependabot configuration
- Fix workflow failures and add Docker release pipeline

### Documentation

- Update for v.0.8 (#262)
- Add comprehensive SKILL.md contribution guide
- Add CLAUDE.md to provide project guidance for AI agents.
- Update and expand documentation, and refine internal pattern analysis definitions and indexes
- Update Docker image references to GHCR and add GHCR build and push instructions.
- Improve readability in dev setup troubleshooting by adding blank lines around a code block.
- Add branding configuration to env reference, .env.example, and QUICKSTART (Phase 8)
- Add generation commands for security-sensitive environment variables
- Sync documentation with branding, embedding, and workflow changes
- Clarify KMP_DUPLICATE_LIB_OK usage in env reference and example
- Remove showcase video link from README.md
- Remove installation video link and add 'Forked From' section.

### Edit

- Changed mcp.py to mcp_handler.py to prevent potential import confusion between 'mcp' package and 'mcp.py'. Edited dockerfile to 'latest' so it doesnt spin up old builds after image creation. Also edited preinstall to ensure the mcp related dependencies can load non-interactive.
- Initialize will now attempt to ensure all mcps are globally installed when the system starts.
- Cleaned up the unneeded mcp config in agent.py
- Cleaned up MCP logs and check attempts.
- Removed unneeded dependencies to slim images for dockerfile install and cuda.
- Get_terminal_output function in code_execution_tool.py is now enhanced to detect common shell prompt patterns (like (venv) ...$, root@...:~#, etc.) using regex. When such a prompt is detected in the output, the function will immediately break and return the output, rather than waiting for the full timeout.
- Code Exe Md to discourage multi-line f.write() calls. (prevent UI errors during code execution tool)
- Prevent the FAISS/KeyError (or any extension error) from crashing agent loop at the agent.py level. The call to self.call_extensions("message_loop_prompts", ...) in prepare_prompt is now wrapped in a try/except block.
- Revised problem solving/bug fixing guidance to discourage common indentation-error prone methods.
- Code Exe Md prompt to further discourse line by line edits, multiple seperate f.write calls, complex string manipulation. encouraged reading, implement fix, and check syntax. context a little bulky but working for now.
- Team Agent System Prompts
- Loop detection now trunacates the looped info so we flood the LLM with less repeated context.
- Encourage cat > EOF multiline edits for code and documentation
- Changed mcp.py to mcp_handler.py to prevent potential import confusion between 'mcp' package and 'mcp.py'. Edited dockerfile to 'latest' so it doesnt spin up old builds after image creation. Also edited preinstall to ensure the mcp related dependencies can load non-interactive.
- Initialize will now attempt to ensure all mcps are globally installed when the system starts.
- Slimmed context of code exe md prompt
- Cleaned up the unneeded mcp config in agent.py
- Cleaned up MCP logs and check attempts.
- Removed unneeded dependencies to slim images for dockerfile install and cuda.

### Features

- Fullscreen chat input (#269)
- Attachment setup
- Openai-whisper voice input
- Attachments preview and sending (file, code, imgs)
- Work_dir file manager
- Speech to text settings
- Copy text button, nudge & fix: various styles
- Chat model VISION support for user and tool msg attachments
- Files.get_subdirectories include and exclude can now be lists
- Container process supervision with sueprvisord
- API: support api_key and localhost without auth, signal handler for term/int
- TaskScheduler - backend mechanics
- TaskScheduler - frontend tabbed display chats tasks
- Tabbed Settings - implement support and move existing settings to 3 tab categories
- Tunnel Manager
- Deduplicate and optimize memory similarity threshold (#389)
- Embedded MCP server for messaging with agent-zero
- Implement support for MCP Servers (Claude Tools) - Part 1 Stdio Servers
- MCP initial support for sse servers (Part 2)
- Deep research agent as prompt folder (#408)
- Implement support for MCP Servers (Claude Tools) - Part 1 Stdio Servers
- MCP initial support for sse servers (Part 2)
- *(ui)* Add tunnel provider selection in settings
- *(ui)* Add provider state to settings modal
- *(ui)* Send tunnel provider to backend
- *(api)* Handle tunnel provider in tunnel api
- *(tunnel)* Implement tunnel provider switching
- Update browser_use to v2 (0.2.5)
- DocumentQuery initial version
- Add rfc_files functions and fix pdf handling for image pdfs
- *(prompt)* Encourage markdown formatting in AI responses
- *(webui)* Render markdown in response bubbles
- *(webui)* Simplify katex rendering delimiters
- *(webui)* Render file paths as clickable links
- Backup and Restore first version
- Improve research prompts and knowledge_tool prompt
- Prompt Profiles for subordinate agent, prompt folder metadata, prompt plugins
- Make subordinate tool prompt more explicit about subtasks
- Prompt plugins - remove some debug statements
- Add developer agent prompt folder/profile
- Thought summaries in agent generation headline
- Add support for 'streamable http transport' mcp servers
- Memory consolidation
- Initial message in chat (WIP, not working)
- Initial message now after first user message (working)
- Change initial message remove question how to help
- Show qr code next to flare tunnel address
- Streamable HTTP Server implementation
- A2A Client/Server Implementation
- Notifications backend system and frontend display
- Frontend-only notifications and test button for them
- Implement enhanced message action buttons with copy and TTS functionality
- Make agentcontexttype background invisible to user (#653)
- External API Endpoints
- Support copy&pasting of last tool result into next call
- *(settings)* Add LiteLLM global params
- Add support for extra HTTP headers in Browser Agent
- Add retry logic for transient LiteLLM errors
- Kali upgrade python3.13
- Memory dashboard first version
- Add session state tracking for code execution
- Separate timeouts for code exec and output (#739)
- Add CometAPI provider
- Add support for agent and project on API
- Microsoft Dev Tunnels
- Complete SKILL.md standard implementation - replace instruments
- Add comprehensive SKILL.md skills and remove legacy instruments
- Add development framework support with skill system and UI
- Skills list UI and APIs
- Enhance agent's internal knowledge, project management, and tool capabilities with a new memory system and prompt refinements.
- Add `hk` for linting and commit hooks, `mise` for environment management, `cliff` for CLI, and `drift` for code analysis, updating ignore files accordingly.
- Add GitHub Actions CI/CD workflows, drift analysis tasks, and codebase pattern data
- Add a new "Modal Patterns Detector" to the approved components patterns.
- Document new development tooling, including mise, hk, DriftDetect, and CI/CD workflows, and update quick start instructions.
- Update project fork details, Docker image source, and regenerate drift patterns and audit snapshots.
- Introduce multi-platform Docker buildx setup and clarify image build/push instructions.
- Introduce `overrides.txt` and integrate it into Docker builds to apply dependency overrides, updating documentation to explain its use.
- Add Azure OpenAI embedding support via LiteLLM Proxy with env-var configuration
- Add centralized branding module and API endpoint (Phase 1)
- Add Alpine.js branding store and update frontend UI text (Phase 2)
- Update login page with Jinja2 branding and add dynamic PWA manifest (Phase 3)
- Replace Agent Zero strings in Python banners, notifications, and CLI (Phase 4)
- Inject brand_name into all prompt templates via Agent methods (Phase 5)
- Update HTTP headers and model provider config with branding (Phase 6)
- Update backup naming, MCP/A2A server descriptions with branding (Phase 7)
- Add branding tests and fix remaining user-facing references (Phase 9)
- Replace A0 abbreviation branding with dynamic/neutral text (Phase 10)
- Rename project from Agent Zero to Apollos AI and update associated agent files and configuration.

### Fix

- Dirty_jason.py the_parse_number method will gracefully handle cases where the parsed string is just '+', '-', or empty, returning it as a string instead of raising a ValueError.
- Input tool session management
- Prevent auto-send when pressing Enter with a non-English input method (#700)
- Proper task cancellation in scheduler, leakage in defer.py
- API keys saved with correct API_KEY_ prefix
- Remove hard-coded timeout caps on MCP tool execution

### Miscellaneous Tasks

- Comments fixes
- Replace print with PrintStyle
- Cleanup comments
- Comments cleanup
- Migrate dependency management to uv, update requirements, and refine various helper, API, and extension modules.
- Update DriftDetect pattern indexes and exclude .drift/ from large file check
- Add LiteLLM Proxy provider, env-var base URLs, updated docs and tooling
- Update mise.lock tool versions (hk 1.36, ruff 0.15)
- Update .env.example with LiteLLM Proxy defaults and correct brand URL
- Bump apollos-ai version from 0.1.0 to 0.2.0

### Refactor

- Modals css
- Css, style: toasts, fix: z-index
- Remove ModelProvider enum
- Extract model provider config to YAML file
- Standardize model provider configuration
- Update backend logic
- File-browser component
- Modals styles cleanup and subdirectories
- *(webui)* Migrate welcome screen to component system architecture
- Clean up banner extensions
- Migrate user data to usr/ + update frontend paths
- Apply extensive code formatting, cleanup, and minor adjustments across the codebase, including the addition of Biome configuration.
- Replace automated rate limiter tests with a manual test and apply minor formatting adjustments across various files.

### Scheduler

- Use convenience methods for logging of special messages

### Styling

- New action buttons + ghost buttons
- Polishing and consistency
- Css cleanup and fix for mobile mem-dashboard; projects css polishing

### Update

- Improved MCP setup and config, async handling for sessions, auto mcp install if present in settings config (on compose)
- Improved MCP setup and config, async handling for sessions, auto mcp install if present in settings config (on compose)

### Updated

- Mcp setup documentation to help guide first time users.
- Mcp setup documentation to help guide first time users.

### WIP

- Docker runtime
- Docker runtime

### Agent

- Retry on critical error

### Backend

- Add mcp log type

### Bugfix

- Settings delta clearing auth

### Cleanup

- Webui folder cleanup (history)

### Migration

- Add overwrite support for .env migration
- Reload .env after moving to usr/ to update config
- Force overwrite for scheduler, knowledge, and instruments dirs
- Correct custom knowledge directory path mapping

### Ssh

- Disable systemd OSC metadata

### Ui

- Better Microsoft Dev Tunnels login design
- Streamline sidebar buttons, add dropdown component
- Process group metrics polishing, group completion bugfix
- Message queue polishing, scrollbars unified
- Scroll stabilization
- Autoscroll polish, image preview sizes reduces
- Welcome screen, queue input, interverntions
- Scroll/collapse fixes
- Response rendering IDs fix
- Fix browser step code

<!-- generated by git-cliff -->
