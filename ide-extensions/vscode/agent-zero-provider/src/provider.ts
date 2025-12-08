import * as vscode from "vscode";
import * as https from "https";
import * as http from "http";

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

  private contextId: string | undefined;
  private context: vscode.ExtensionContext;

  constructor(context: vscode.ExtensionContext) {
    this.context = context;
    // Restore context ID from storage
    this.contextId = context.globalState.get("agentZero.contextId");
  }

  refreshModels(): void {
    this._onDidChangeLanguageModelChatInformation.fire();
  }

  private getConfig() {
    const config = vscode.workspace.getConfiguration("agentZero");
    return {
      apiHost: config.get<string>("apiHost") || "http://localhost:55000",
      apiKey: config.get<string>("apiKey") || "",
      timeout: config.get<number>("timeout") || 300000, // 5 minute default
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
    contextParts.push("You are connected via VS Code extension. The user's workspace is mapped to the container as follows:\n");

    const workspacePaths = workspaceFolders.map((folder) => {
      const localPath = folder.uri.fsPath;
      let containerMappedPath = localPath;
      
      // Map host path to container path if configured
      if (hostPath && localPath.startsWith(hostPath)) {
        containerMappedPath = localPath.replace(hostPath, containerPath);
      } else if (hostPath) {
        // If hostPath is configured but doesn't match, warn
        containerMappedPath = `${containerPath}${localPath}`;
      }
      
      contextParts.push(`- Local: ${localPath}`);
      contextParts.push(`  Container: ${containerMappedPath}`);
      
      return containerMappedPath;
    });

    contextParts.push(`\nWorking directories (use these container paths in your responses): ${workspacePaths.join(", ")}`);
    contextParts.push("\nIMPORTANT: If these paths don't exist in the container, the workspace may not be mounted.");
    contextParts.push("To mount the workspace, ensure Docker was started with: -v <hostPath>:<containerPath>");
    contextParts.push(`Example: docker run -v ${hostPath || "/path/to/projects"}:${containerPath} ...`);

    // Add git repository information if available
    for (const folder of workspaceFolders) {
      try {
        const gitUri = vscode.Uri.joinPath(folder.uri, ".git");
        const gitExists = await vscode.workspace.fs.stat(gitUri).then(
          () => true,
          () => false
        );
        
        if (gitExists) {
          const repoName = folder.name;
          contextParts.push(`\nGit Repository: ${repoName}`);
          contextParts.push(`Repository root (container): ${workspacePaths[workspaceFolders.indexOf(folder)]}`);
          contextParts.push("You can read and modify files in this repository. Use the container paths above.");
        }
      } catch (e) {
        // Ignore errors checking for git
      }
    }

    // Add active file information
    const activeFile = vscode.window.activeTextEditor?.document.uri.fsPath;
    if (activeFile) {
      let activeFilePath = activeFile;
      if (hostPath && activeFile.startsWith(hostPath)) {
        activeFilePath = activeFile.replace(hostPath, containerPath);
      } else if (hostPath) {
        activeFilePath = `${containerPath}${activeFile}`;
      }
      contextParts.push(`\nCurrently open file: ${activeFilePath}`);
    }

    // Add file tree information (list some files to help Agent Zero understand the structure)
    try {
      const files = await vscode.workspace.findFiles(
        "**/*",
        "**/{node_modules,.git,.venv,__pycache__}/**",
        20 // Limit to 20 files to avoid huge context
      );
      if (files.length > 0) {
        contextParts.push("\nSample files in workspace:");
        for (const file of files.slice(0, 10)) {
          let filePath = file.fsPath;
          if (hostPath && filePath.startsWith(hostPath)) {
            filePath = filePath.replace(hostPath, containerPath);
          } else if (hostPath) {
            filePath = `${containerPath}${filePath}`;
          }
          const relativePath = vscode.workspace.asRelativePath(file);
          contextParts.push(`  - ${relativePath} → ${filePath}`);
        }
        if (files.length > 10) {
          contextParts.push(`  ... and ${files.length - 10} more files`);
        }
      }
    } catch (e) {
      // Ignore errors getting file list
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
        contextId: this.contextId,
      },
      {
        id: "agent-zero-fresh",
        name: "Agent Zero (New Session)",
        family: "agent-zero",
        version: "1.0.0",
        maxInputTokens: 128000,
        maxOutputTokens: 16000,
        tooltip: "Start a fresh Agent Zero session",
        detail: "New conversation context",
        capabilities: {
          imageInput: false,
          toolCalling: true,
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

    // Append workspace context so Agent Zero knows where files are
    const workspaceContext = await this.getWorkspaceContext();
    if (workspaceContext) {
      messageText = messageText + workspaceContext;
    }

    // Check for cancellation
    if (token.isCancellationRequested) {
      throw new Error("Request cancelled");
    }

    if (useStreaming) {
      // Try streaming mode via async message + polling
      // If it fails (e.g., CSRF token required when login is enabled), fall back to sync mode
      try {
        await this.streamResponse(
          apiHost,
          apiKey,
          messageText,
          model.id === "agent-zero" ? this.contextId : undefined,
          pollInterval,
          timeout,
          progress,
          token
        );
      } catch (error) {
        // If streaming fails due to CSRF/auth requirements, fall back to API endpoint
        if (
          error instanceof Error &&
          (error.message.includes("CSRF") ||
            error.message.includes("302") ||
            error.message.includes("login"))
        ) {
          console.log(
            "Streaming mode failed (likely CSRF/auth issue), falling back to non-streaming API endpoint"
          );
          await this.sendSyncMessage(
            apiHost,
            apiKey,
            messageText,
            model.id === "agent-zero" ? this.contextId : undefined,
            timeout,
            progress,
            token
          );
        } else {
          // Re-throw other errors
          throw error;
        }
      }
    } else {
      // Use non-streaming mode (original implementation)
      await this.sendSyncMessage(
        apiHost,
        apiKey,
        messageText,
        model.id === "agent-zero" ? this.contextId : undefined,
        timeout,
        progress,
        token
      );
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
  ): Promise<void> {
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

      if (response.context_id) {
        this.contextId = response.context_id;
        await this.context.globalState.update(
          "agentZero.contextId",
          this.contextId
        );
      }

      if (response.response) {
        progress.report(new vscode.LanguageModelTextPart(response.response));
      }
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

  private async streamResponse(
    apiHost: string,
    apiKey: string,
    messageText: string,
    contextId: string | undefined,
    pollInterval: number,
    timeout: number,
    progress: vscode.Progress<vscode.LanguageModelResponsePart>,
    token: vscode.CancellationToken
  ): Promise<void> {
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
      if (newContextId) {
        this.contextId = newContextId;
        await this.context.globalState.update(
          "agentZero.contextId",
          this.contextId
        );
      }

      // Step 2: Poll for streaming updates
      await this.pollForUpdates(
        apiHost,
        newContextId,
        pollInterval,
        timeout,
        progress,
        token
      );
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
      // Check timeout
      if (Date.now() - startTime > timeout) {
        throw new Error("Request timeout - Agent Zero task took too long");
      }

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
    timeout: number = 300000 // 5 minute default
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

