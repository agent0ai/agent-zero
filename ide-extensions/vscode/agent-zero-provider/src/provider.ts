import * as vscode from "vscode";
import * as https from "https";
import * as http from "http";
import * as crypto from "crypto";

interface AgentZeroResponse {
  context_id: string;
  response: string;
  error?: string;
}

interface AgentZeroAsyncResponse {
  context: string;
  error?: string;
}

interface AgentZeroPollLog {
  no: number;
  id: string;
  type: string;
  heading: string;
  content: string;
  temp: boolean;
  kvps?: {
    finished?: boolean;
    headline?: string;
    tool_name?: string;
    tool_args?: unknown;
  };
}

interface AgentZeroPollResponse {
  context: string;
  log_version: number;
  log_guid: string;
  log_progress: string;
  log_progress_active: boolean;
  logs: AgentZeroPollLog[];
  paused: boolean;
  error?: string;
}

interface AgentZeroModelInfo extends vscode.LanguageModelChatInformation {
  contextId?: string;
}

export class AgentZeroChatModelProvider
  implements vscode.LanguageModelChatProvider<AgentZeroModelInfo>
{
  private _onDidChangeLanguageModelChatInformation =
    new vscode.EventEmitter<void>();
  readonly onDidChangeLanguageModelChatInformation =
    this._onDidChangeLanguageModelChatInformation.event;

  private context: vscode.ExtensionContext;
  // Track contextId per chat session (keyed by session ID)
  private sessionContexts: Map<string, string> = new Map();
  // Track when each session was last accessed (to detect stale sessions)
  private sessionTimestamps: Map<string, number> = new Map();
  // Map from conversation fingerprint to session ID (for finding existing sessions)
  // Fingerprint is based on first user message + message count to make it more unique
  private conversationFingerprintToSession: Map<string, string> = new Map();
  // Track message counts per session to help identify sessions
  private sessionMessageCounts: Map<string, number> = new Map();

  constructor(context: vscode.ExtensionContext) {
    this.context = context;
  }

  refreshModels(): void {
    this._onDidChangeLanguageModelChatInformation.fire();
  }

  private getConfig() {
    const config = vscode.workspace.getConfiguration("agentZero");
    return {
      apiHost: config.get<string>("apiHost") || "http://localhost:55000",
      apiKey: config.get<string>("apiKey") || "",
      timeout: config.get<number>("timeout") || Number.MAX_SAFE_INTEGER, // Effectively no timeout (for very long tasks)
      hostPath: config.get<string>("hostPath") || "",
      containerPath: config.get<string>("containerPath") || "/a0-01",
      useStreaming: config.get<boolean>("useStreaming") ?? true, // Default to streaming
      pollInterval: config.get<number>("pollInterval") || 100, // Poll every 100ms
    };
  }

  private async getWorkspaceContext(): Promise<string> {
    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (!workspaceFolders || workspaceFolders.length === 0) {
      return "";
    }

    const { hostPath, containerPath } = this.getConfig();
    const contextParts: string[] = [];
    
    contextParts.push("\n\n[WORKSPACE CONTEXT]");

    // Calculate workspace paths
    const workspacePaths = workspaceFolders.map((folder) => {
      const localPath = folder.uri.fsPath;
      let containerMappedPath = localPath;
      
      // Normalize container path (remove trailing slashes)
      const normalizedContainer = containerPath.replace(/\/+$/, "");
      
      // Expand ~ in hostPath if present
      let expandedHostPath = hostPath;
      if (hostPath && hostPath.startsWith("~/")) {
        const homeDir = process.env.HOME || process.env.USERPROFILE || "";
        expandedHostPath = hostPath.replace("~", homeDir);
      }
      
      // Map host path to container path if configured
      if (expandedHostPath && localPath.startsWith(expandedHostPath)) {
        // Direct replacement: replace hostPath with containerPath
        const remainingPath = localPath.substring(expandedHostPath.length).replace(/^\/+/, "");
        containerMappedPath = remainingPath ? `${normalizedContainer}/${remainingPath}` : normalizedContainer;
      } else if (expandedHostPath) {
        // If hostPath is configured but workspace is not directly under it,
        // try to extract the actual directory name from the path
        // First, try to see if workspace path contains hostPath as a parent
        // If not, extract the last directory component from localPath
        const pathParts = localPath.split(/[/\\]/).filter(p => p.length > 0);
        const lastDirName = pathParts[pathParts.length - 1];
        
        // Try multiple possibilities:
        // 1. Last directory name from path
        // 2. Workspace folder display name
        // Store both as alternatives
        const workspaceName = folder.name;
        containerMappedPath = `${normalizedContainer}/${lastDirName}`;
      } else {
        // If hostPath not configured, extract directory name from path
        const pathParts = localPath.split(/[/\\]/).filter(p => p.length > 0);
        const lastDirName = pathParts[pathParts.length - 1];
        containerMappedPath = `${normalizedContainer}/${lastDirName}`;
      }
      
      return containerMappedPath;
    });

    // CRITICAL: File search paths (first, most prominent)
    const normalizedContainer = containerPath.replace(/\/+$/, "");
    contextParts.push("\nCRITICAL - File Search Paths:");
    contextParts.push("When user mentions a file, ALWAYS search in these container paths FIRST (in order):");
    workspacePaths.forEach((path, index) => {
      contextParts.push(`  ${index + 1}. ${path}`);
    });
    // Add alternative paths based on workspace folder name and directory name
    workspaceFolders.forEach((folder) => {
      const folderNamePath = `${normalizedContainer}/${folder.name}`;
      const localPathParts = folder.uri.fsPath.split(/[/\\]/).filter(p => p.length > 0);
      const lastDirName = localPathParts[localPathParts.length - 1];
      const lastDirPath = `${normalizedContainer}/${lastDirName}`;
      
      // Add alternatives if they differ from the primary path
      const alternatives: string[] = [];
      if (!workspacePaths.includes(folderNamePath) && folderNamePath !== workspacePaths[0]) {
        alternatives.push(folderNamePath);
      }
      if (!workspacePaths.includes(lastDirPath) && lastDirPath !== workspacePaths[0] && lastDirPath !== folderNamePath) {
        alternatives.push(lastDirPath);
      }
      
      if (alternatives.length > 0) {
        contextParts.push(`  Alternative paths to try if primary path doesn't exist:`);
        alternatives.forEach(alt => {
          contextParts.push(`    - ${alt}`);
        });
        contextParts.push(`  If paths don't exist, run: ls -la ${normalizedContainer} | grep -i "${folder.name.replace(/\s+/g, '.*')}" to find similar directory names`);
      }
    });
    contextParts.push("For simple filenames (e.g., 'inquiries.docx'), check workspace root first:");
    workspacePaths.forEach((path) => {
      // Check if path contains spaces and show quoted version
      const needsQuoting = path.includes(" ");
      const quotedPath = needsQuoting ? `"${path}"` : path;
      contextParts.push(`  - ${quotedPath}/inquiries.docx`);
    });
    contextParts.push("Do NOT search in /root, /home, or other locations unless explicitly asked.");
    contextParts.push("\nIf primary path doesn't exist:");
    contextParts.push("  1. First, verify the workspace directory exists: ls -la <primary_path>");
    contextParts.push("  2. If it doesn't exist, list /a0-01 to find the actual directory name:");
    workspaceFolders.forEach((folder) => {
      const searchTerm = folder.name.replace(/\s+/g, ".*");
      contextParts.push(`     ls -la ${normalizedContainer} | grep -i "${searchTerm}"`);
    });
    contextParts.push("  3. Once you find the correct directory, use that path for all file operations.");
    
    // Add warning about spaces in paths
    const hasSpaces = workspacePaths.some(p => p.includes(" "));
    if (hasSpaces) {
      contextParts.push("\nIMPORTANT - Paths contain spaces:");
      contextParts.push("ALWAYS quote paths with spaces when using them in shell commands.");
      workspacePaths.forEach((path) => {
        if (path.includes(" ")) {
          contextParts.push(`  Use: "${path}" (with quotes)`);
          contextParts.push(`  NOT: ${path} (without quotes)`);
        }
      });
    }

    // CRITICAL: Output location (second, prominent)
    const primaryWorkspacePath = workspacePaths[0];
    const needsQuoting = primaryWorkspacePath.includes(" ");
    const quotedWorkspacePath = needsQuoting ? `"${primaryWorkspacePath}"` : primaryWorkspacePath;
    
    contextParts.push(`\nCRITICAL - Output Location:`);
    contextParts.push(`NEVER save files to /root, /home, or any other directory.`);
    contextParts.push(`ALWAYS save ALL output files to this workspace directory:`);
    contextParts.push(`  ${primaryWorkspacePath}`);
    if (needsQuoting) {
      contextParts.push(`Example: If creating 'output.pdf', save to: ${quotedWorkspacePath}/output.pdf`);
      contextParts.push(`Example: If creating 'inquiries.pdf', save to: ${quotedWorkspacePath}/inquiries.pdf`);
    } else {
      contextParts.push(`Example: If creating 'output.pdf', save to: ${primaryWorkspacePath}/output.pdf`);
      contextParts.push(`Example: If creating 'inquiries.pdf', save to: ${primaryWorkspacePath}/inquiries.pdf`);
    }
    contextParts.push(`Before saving any file, verify the path starts with: ${primaryWorkspacePath}`);

    // Working directory
    contextParts.push(`\nWorking directory: ${primaryWorkspacePath}`);
    contextParts.push(`Change to this directory before running commands: cd ${quotedWorkspacePath}`);
    if (needsQuoting) {
      contextParts.push(`Always use quotes when referencing this path in commands: ${quotedWorkspacePath}`);
    }

    // Path mapping (if configured, concise)
    if (hostPath) {
      contextParts.push(`\nPath mapping: ${hostPath} → ${containerPath}`);
    }

    // Git repository info (condensed)
    for (const folder of workspaceFolders) {
      try {
        const gitUri = vscode.Uri.joinPath(folder.uri, ".git");
        const gitExists = await vscode.workspace.fs.stat(gitUri).then(
          () => true,
          () => false
        );
        
        if (gitExists) {
          const repoName = folder.name;
          const repoIndex = workspaceFolders.indexOf(folder);
          const repoContainerPath = workspacePaths[repoIndex];
          contextParts.push(`\nGit repo: ${repoName} → ${repoContainerPath}`);
        }
      } catch (e) {
        // Ignore errors checking for git
      }
    }

    contextParts.push("\n[/WORKSPACE CONTEXT]\n");
    return contextParts.join("\n");
  }

  async provideLanguageModelChatInformation(
    options: vscode.PrepareLanguageModelChatModelOptions,
    token: vscode.CancellationToken
  ): Promise<AgentZeroModelInfo[]> {
    const { apiHost, apiKey } = this.getConfig();

    // Check if API key is configured
    if (!apiKey && !options.silent) {
      const configure = await vscode.window.showWarningMessage(
        "Agent Zero API key not configured",
        "Configure Now"
      );
      if (configure) {
        await vscode.commands.executeCommand("agent-zero.configure");
      }
      return [];
    }

    if (!apiKey) {
      return [];
    }

    // Check if Agent Zero is reachable
    try {
      const healthCheck = await this.makeRequest<{ status: string }>(
        `${apiHost}/health`,
        "GET"
      );
      if (!healthCheck) {
        console.log("Agent Zero not reachable");
        return [];
      }
    } catch (error) {
      console.log("Agent Zero health check failed:", error);
      if (!options.silent) {
        vscode.window.showWarningMessage(
          `Cannot connect to Agent Zero at ${apiHost}. Is the container running?`
        );
      }
      return [];
    }

    // Return available models
    // Agent Zero acts as a single model that can use various backends
    return [
      {
        id: "agent-zero",
        name: "Agent Zero",
        family: "agent-zero",
        version: "1.0.0",
        maxInputTokens: 128000, // Varies by backend model
        maxOutputTokens: 16000,
        tooltip:
          "Autonomous AI agent with code execution, file operations, and web browsing",
        detail: "Runs in Docker container",
        capabilities: {
          imageInput: false, // Could be true if Agent Zero supports it
          toolCalling: true, // Agent Zero has extensive tool capabilities
        },
      },
    ];
  }

  async provideLanguageModelChatResponse(
    model: AgentZeroModelInfo,
    messages: readonly vscode.LanguageModelChatRequestMessage[],
    options: vscode.ProvideLanguageModelChatResponseOptions,
    progress: vscode.Progress<vscode.LanguageModelResponsePart>,
    token: vscode.CancellationToken
  ): Promise<void> {
    const { apiHost, apiKey, useStreaming, pollInterval, timeout } =
      this.getConfig();

    if (!apiKey) {
      throw new Error(
        'Agent Zero API key not configured. Run "Configure Agent Zero" command.'
      );
    }

    // Convert messages to Agent Zero format
    // We'll send the last user message as the main message
    const userMessages = messages.filter(
      (m) => m.role === vscode.LanguageModelChatMessageRole.User
    );
    const lastUserMessage = userMessages[userMessages.length - 1];

    if (!lastUserMessage) {
      throw new Error("No user message found");
    }

    // Extract text content from the message
    let messageText = lastUserMessage.content
      .filter(
        (part): part is vscode.LanguageModelTextPart =>
          part instanceof vscode.LanguageModelTextPart
      )
      .map((part) => part.value)
      .join("\n");

    if (!messageText) {
      throw new Error("No text content in message");
    }

    // Check if this is a new chat window (only 1 user message, no assistant messages)
    const assistantMessages = messages.filter(
      (m) => m.role === vscode.LanguageModelChatMessageRole.Assistant
    );
    const isNewChatWindow = userMessages.length === 1 && assistantMessages.length === 0;
    
    // Use first message hash as stable session identifier
    // This remains constant as the conversation continues
    const firstUserMessage = userMessages[0];
    const firstUserText = firstUserMessage
      ? firstUserMessage.content
          .filter(
            (part): part is vscode.LanguageModelTextPart =>
              part instanceof vscode.LanguageModelTextPart
          )
          .map((part) => part.value)
          .join("\n")
      : messageText;
    const firstMessageHash = crypto.createHash("sha256").update(firstUserText.substring(0, 500)).digest("hex").substring(0, 16);
    
    // Clean up old sessions
    const now = Date.now();
    const oneHourAgo = now - 60 * 60 * 1000;
    for (const [sid, timestamp] of this.sessionTimestamps.entries()) {
      if (timestamp < oneHourAgo) {
        this.sessionContexts.delete(sid);
        this.sessionTimestamps.delete(sid);
        this.sessionMessageCounts.delete(sid);
        for (const [hash, mappedSid] of this.conversationFingerprintToSession.entries()) {
          if (mappedSid === sid) {
            this.conversationFingerprintToSession.delete(hash);
          }
        }
      }
    }
    
    // Determine session: new chat windows always start fresh
    let sessionId: string;
    let sessionContextId: string | undefined;
    
    if (isNewChatWindow) {
      // New chat window - always start fresh, even if same first message as old chat
      const timestamp = Date.now();
      const random = crypto.randomBytes(8).toString("hex");
      sessionId = `${timestamp}-${random}`;
      this.conversationFingerprintToSession.set(firstMessageHash, sessionId);
      this.sessionMessageCounts.set(sessionId, userMessages.length);
      sessionContextId = undefined;
    } else {
      // Continuing conversation - look up session by first message hash
      const foundSessionId = this.conversationFingerprintToSession.get(firstMessageHash);
      
      // If found session has contextId and is recent -> continue, otherwise -> start fresh
      if (foundSessionId && 
          this.sessionContexts.has(foundSessionId) && 
          this.sessionContexts.get(foundSessionId) &&
          this.sessionTimestamps.get(foundSessionId) && 
          this.sessionTimestamps.get(foundSessionId)! > oneHourAgo) {
        // Continue existing session
        sessionId = foundSessionId;
        sessionContextId = this.sessionContexts.get(sessionId);
        this.sessionMessageCounts.set(sessionId, userMessages.length);
      } else {
        // Start new session
        const timestamp = Date.now();
        const random = crypto.randomBytes(8).toString("hex");
        sessionId = `${timestamp}-${random}`;
        this.conversationFingerprintToSession.set(firstMessageHash, sessionId);
        this.sessionMessageCounts.set(sessionId, userMessages.length);
        sessionContextId = undefined;
      }
    }
    
    this.sessionTimestamps.set(sessionId, now);

    // Send workspace context only if no contextId (new session)
    if (!sessionContextId) {
      const workspaceContext = await this.getWorkspaceContext();
      if (workspaceContext) {
        messageText = messageText + workspaceContext;
      }
    }

    // Check for cancellation
    if (token.isCancellationRequested) {
      throw new Error("Request cancelled");
    }

    if (useStreaming) {
      // Try streaming mode via async message + polling
      // If it fails (e.g., CSRF token required when login is enabled), fall back to sync mode
      try {
        const newContextId = await this.streamResponse(
          apiHost,
          apiKey,
          messageText,
          sessionContextId,
          pollInterval,
          timeout,
          progress,
          token
        );
        // Update session contextId if Agent Zero returned a new one
        if (newContextId) {
          this.sessionContexts.set(sessionId, newContextId);
        }
      } catch (error) {
        // If context not found, retry as new session (contextId expired)
        const errorMessage = error instanceof Error ? error.message : String(error);
        if (errorMessage.includes("Context not found") || 
            (errorMessage.includes("404") && errorMessage.includes("Context"))) {
          console.log(
            "Context not found, retrying as new session"
          );
          // Clear the invalid contextId and retry
          sessionContextId = undefined;
          this.sessionContexts.delete(sessionId);
          // Retry without contextId
          try {
            const newContextId = await this.streamResponse(
              apiHost,
              apiKey,
              messageText,
              undefined,
              pollInterval,
              timeout,
              progress,
              token
            );
            if (newContextId) {
              this.sessionContexts.set(sessionId, newContextId);
            }
          } catch (retryError) {
            // If streaming fails due to CSRF/auth requirements, fall back to API endpoint
            if (
              retryError instanceof Error &&
              (retryError.message.includes("CSRF") ||
                retryError.message.includes("302") ||
                retryError.message.includes("login"))
            ) {
              console.log(
                "Streaming mode failed (likely CSRF/auth issue), falling back to non-streaming API endpoint"
              );
              const fallbackContextId = await this.sendSyncMessage(
                apiHost,
                apiKey,
                messageText,
                undefined,
                timeout,
                progress,
                token
              );
              if (fallbackContextId) {
                this.sessionContexts.set(sessionId, fallbackContextId);
              }
            } else {
              throw retryError;
            }
          }
        } else if (
          error instanceof Error &&
          (error.message.includes("CSRF") ||
            error.message.includes("302") ||
            error.message.includes("login"))
        ) {
          console.log(
            "Streaming mode failed (likely CSRF/auth issue), falling back to non-streaming API endpoint"
          );
          const fallbackContextId = await this.sendSyncMessage(
            apiHost,
            apiKey,
            messageText,
            sessionContextId,
            timeout,
            progress,
            token
          );
          // Update session contextId if Agent Zero returned a new one
          if (fallbackContextId) {
            this.sessionContexts.set(sessionId, fallbackContextId);
          }
        } else {
          // Re-throw other errors
          throw error;
        }
      }
    } else {
      // Use non-streaming mode (original implementation)
      try {
        const syncContextId = await this.sendSyncMessage(
          apiHost,
          apiKey,
          messageText,
          sessionContextId,
          timeout,
          progress,
          token
        );
        // Update session contextId if Agent Zero returned a new one
        if (syncContextId) {
          this.sessionContexts.set(sessionId, syncContextId);
        }
      } catch (error) {
        // If context not found, retry as new session (contextId expired)
        const errorMessage = error instanceof Error ? error.message : String(error);
        if (errorMessage.includes("Context not found") || 
            (errorMessage.includes("404") && errorMessage.includes("Context"))) {
          console.log(
            "Context not found, retrying as new session"
          );
          // Clear the invalid contextId and retry
          sessionContextId = undefined;
          this.sessionContexts.delete(sessionId);
          const syncContextId = await this.sendSyncMessage(
            apiHost,
            apiKey,
            messageText,
            undefined,
            timeout,
            progress,
            token
          );
          if (syncContextId) {
            this.sessionContexts.set(sessionId, syncContextId);
          }
        } else {
          throw error;
        }
      }
    }
  }

  private async sendSyncMessage(
    apiHost: string,
    apiKey: string,
    messageText: string,
    contextId: string | undefined,
    timeout: number,
    progress: vscode.Progress<vscode.LanguageModelResponsePart>,
    token: vscode.CancellationToken
  ): Promise<string | undefined> {
    const requestBody: {
      message: string;
      lifetime_hours: number;
      context_id?: string;
    } = {
      message: messageText,
      lifetime_hours: 24,
    };

    if (contextId) {
      requestBody.context_id = contextId;
    }

    try {
      progress.report(new vscode.LanguageModelTextPart(""));

      const response = await this.makeRequest<AgentZeroResponse>(
        `${apiHost}/api_message`,
        "POST",
        requestBody,
        { "X-API-KEY": apiKey },
        token,
        timeout
      );

      if (!response) {
        throw new Error("No response from Agent Zero");
      }

      if (response.error) {
        throw new Error(`Agent Zero error: ${response.error}`);
      }

      if (response.response) {
        progress.report(new vscode.LanguageModelTextPart(response.response));
      }

      // Return contextId for session tracking
      return response.context_id;
    } catch (error) {
      if (error instanceof Error && error.message === "Request cancelled") {
        throw error;
      }
      // Check if this is a "Context not found" error - preserve it for retry logic
      const errorMessage = error instanceof Error ? error.message : String(error);
      if (errorMessage.includes("Context not found") || 
          (errorMessage.includes("404") && errorMessage.includes("Context"))) {
        // Throw a specific error that can be caught and handled
        const contextNotFoundError = new Error("Context not found");
        (contextNotFoundError as any).originalError = error;
        throw contextNotFoundError;
      }
      throw new Error(
        `Agent Zero request failed: ${errorMessage}`
      );
    }
  }

  private async streamResponse(
    apiHost: string,
    apiKey: string,
    messageText: string,
    contextId: string | undefined,
    pollInterval: number,
    timeout: number,
    progress: vscode.Progress<vscode.LanguageModelResponsePart>,
    token: vscode.CancellationToken
  ): Promise<string | undefined> {
    // Step 1: Send async message
    const requestBody: {
      text: string;
      context: string | null;
    } = {
      text: messageText,
      context: contextId || null,
    };

    try {
      // Try to use message_async endpoint (requires CSRF if login is enabled)
      // If it fails, the caller will fall back to api_message
      const asyncResponse = await this.makeRequest<AgentZeroAsyncResponse>(
        `${apiHost}/message_async`,
        "POST",
        requestBody,
        { "Content-Type": "application/json" },
        token,
        30000 // 30 second timeout for initial request
      );

      if (!asyncResponse) {
        throw new Error("No response from Agent Zero");
      }

      if (asyncResponse.error) {
        throw new Error(`Agent Zero error: ${asyncResponse.error}`);
      }

      const newContextId = asyncResponse.context;

      // Step 2: Poll for streaming updates
      await this.pollForUpdates(
        apiHost,
        newContextId || contextId || "",
        pollInterval,
        timeout,
        progress,
        token
      );

      // Return contextId for session tracking
      return newContextId || contextId;
    } catch (error) {
      if (error instanceof Error && error.message === "Request cancelled") {
        throw error;
      }
      throw new Error(
        `Agent Zero request failed: ${
          error instanceof Error ? error.message : String(error)
        }`
      );
    }
  }

  private async pollForUpdates(
    apiHost: string,
    contextId: string,
    pollInterval: number,
    timeout: number,
    progress: vscode.Progress<vscode.LanguageModelResponsePart>,
    token: vscode.CancellationToken
  ): Promise<void> {
    let logVersion = 0;
    let logGuid = "";
    let lastResponseContent = "";
    let isComplete = false;
    const startTime = Date.now();
    const seenLogIds = new Set<string>();

    while (!isComplete && !token.isCancellationRequested) {
      // No timeout for streaming mode - tasks can run indefinitely
      // The user can cancel via VSCode's cancellation token if needed

      try {
        const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
        const pollResponse = await this.makeRequest<AgentZeroPollResponse>(
          `${apiHost}/poll`,
          "POST",
          {
            log_from: logVersion,
            context: contextId,
            timezone: timezone,
          },
          { "Content-Type": "application/json" },
          token,
          10000 // 10 second timeout for poll requests
        );

        if (!pollResponse) {
          await this.sleep(pollInterval);
          continue;
        }

        // Handle context/guid changes (chat reset)
        if (logGuid && pollResponse.log_guid !== logGuid) {
          logVersion = 0;
          seenLogIds.clear();
          lastResponseContent = "";
        }
        logGuid = pollResponse.log_guid;

        // Process new log entries
        if (pollResponse.logs && pollResponse.logs.length > 0) {
          for (const log of pollResponse.logs) {
            const logId = log.id || String(log.no);

            // Skip already processed logs
            if (seenLogIds.has(logId)) {
              continue;
            }
            seenLogIds.add(logId);

            // Stream response content
            if (log.type === "response" && log.content) {
              // Only send new content (delta)
              if (log.content.length > lastResponseContent.length) {
                const newContent = log.content.substring(
                  lastResponseContent.length
                );
                progress.report(new vscode.LanguageModelTextPart(newContent));
                lastResponseContent = log.content;
              } else if (log.content !== lastResponseContent) {
                // Content changed entirely, send it all
                progress.report(new vscode.LanguageModelTextPart(log.content));
                lastResponseContent = log.content;
              }

              // Check if response is finished
              if (log.kvps?.finished) {
                isComplete = true;
              }
            } else if (
              log.type === "agent" &&
              log.kvps?.headline &&
              !log.temp
            ) {
              // Show agent activity (tool usage, thinking, etc.)
              const headline = log.kvps.headline;
              const toolName = log.kvps.tool_name;
              if (toolName && toolName !== "response") {
                progress.report(
                  new vscode.LanguageModelTextPart(`\n\n*${headline}*\n\n`)
                );
              }
            }
          }
        }

        // Check if agent is no longer active (no progress)
        if (
          !pollResponse.log_progress_active &&
          logVersion === pollResponse.log_version &&
          logVersion > 0
        ) {
          // Give it a few more polls to be sure
          await this.sleep(pollInterval * 3);
          const checkResponse = await this.makeRequest<AgentZeroPollResponse>(
            `${apiHost}/poll`,
            "POST",
            { log_from: logVersion, context: contextId, timezone },
            { "Content-Type": "application/json" },
            token,
            10000
          );
          if (
            checkResponse &&
            !checkResponse.log_progress_active &&
            checkResponse.log_version === logVersion
          ) {
            isComplete = true;
          }
        }

        logVersion = pollResponse.log_version;
      } catch (error) {
        // Ignore transient errors during polling, just continue
        console.log("Poll error (retrying):", error);
      }

      await this.sleep(pollInterval);
    }

    if (token.isCancellationRequested) {
      throw new Error("Request cancelled");
    }
  }

  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  async provideTokenCount(
    model: AgentZeroModelInfo,
    text: string | vscode.LanguageModelChatRequestMessage,
    token: vscode.CancellationToken
  ): Promise<number> {
    // Simple token estimation (roughly 4 chars per token)
    let textContent: string;

    if (typeof text === "string") {
      textContent = text;
    } else {
      textContent = text.content
        .filter(
          (part): part is vscode.LanguageModelTextPart =>
            part instanceof vscode.LanguageModelTextPart
        )
        .map((part) => part.value)
        .join("\n");
    }

    return Math.ceil(textContent.length / 4);
  }

  private makeRequest<T>(
    url: string,
    method: "GET" | "POST",
    body?: object,
    headers?: Record<string, string>,
    cancellationToken?: vscode.CancellationToken,
    timeout: number = Number.MAX_SAFE_INTEGER // Effectively no timeout (for very long tasks)
  ): Promise<T | null> {
    return new Promise((resolve, reject) => {
      const parsedUrl = new URL(url);
      const isHttps = parsedUrl.protocol === "https:";
      const httpModule = isHttps ? https : http;

      const requestOptions: http.RequestOptions = {
        hostname: parsedUrl.hostname,
        port: parsedUrl.port || (isHttps ? 443 : 80),
        path: parsedUrl.pathname + parsedUrl.search,
        method,
        headers: {
          "Content-Type": "application/json",
          ...headers,
        },
        timeout, // Use configurable timeout
      };

      const req = httpModule.request(requestOptions, (res) => {
        let data = "";

        res.on("data", (chunk) => {
          data += chunk;
        });

        res.on("end", () => {
          try {
            if (
              res.statusCode &&
              res.statusCode >= 200 &&
              res.statusCode < 300
            ) {
              const parsed = data ? (JSON.parse(data) as T) : null;
              resolve(parsed);
            } else {
              reject(new Error(`HTTP ${res.statusCode}: ${data}`));
            }
          } catch (error) {
            reject(new Error(`Failed to parse response: ${data}`));
          }
        });
      });

      req.on("error", (error) => {
        reject(error);
      });

      req.on("timeout", () => {
        req.destroy();
        reject(new Error("Request timeout"));
      });

      // Handle cancellation
      if (cancellationToken) {
        cancellationToken.onCancellationRequested(() => {
          req.destroy();
          reject(new Error("Request cancelled"));
        });
      }

      if (body && method === "POST") {
        req.write(JSON.stringify(body));
      }

      req.end();
    });
  }
}

