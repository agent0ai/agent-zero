import * as vscode from "vscode";
import { AgentZeroChatModelProvider } from "./provider";

export function activate(context: vscode.ExtensionContext) {
  console.log("Agent Zero Provider activated");

  // Register the language model provider
  const provider = new AgentZeroChatModelProvider(context);
  const disposable = vscode.lm.registerLanguageModelChatProvider(
    "agent-zero",
    provider
  );
  context.subscriptions.push(disposable);

  // Register the configuration command
  const configureCommand = vscode.commands.registerCommand(
    "agent-zero.configure",
    async () => {
      const config = vscode.workspace.getConfiguration("agentZero");

      const apiHost = await vscode.window.showInputBox({
        prompt: "Enter Agent Zero API Host",
        value: config.get("apiHost") || "http://localhost:55000",
        placeHolder: "http://localhost:55000",
      });

      if (apiHost) {
        await config.update(
          "apiHost",
          apiHost,
          vscode.ConfigurationTarget.Global
        );
      }

      const apiKey = await vscode.window.showInputBox({
        prompt: "Enter Agent Zero API Key",
        value: config.get("apiKey") || "",
        placeHolder: "Your API key from Agent Zero Settings",
        password: true,
      });

      if (apiKey) {
        await config.update(
          "apiKey",
          apiKey,
          vscode.ConfigurationTarget.Global
        );
      }

      const hostPath = await vscode.window.showInputBox({
        prompt: "Enter your local Projects path (host machine)",
        value: config.get("hostPath") || "",
        placeHolder: "~/Projects or /path/to/projects",
      });

      if (hostPath) {
        await config.update(
          "hostPath",
          hostPath,
          vscode.ConfigurationTarget.Global
        );
      }

      const containerPath = await vscode.window.showInputBox({
        prompt: "Enter the container mount path (where host path is mounted)",
        value: config.get("containerPath") || "/a0-01",
        placeHolder: "/a0-01",
      });

      if (containerPath) {
        await config.update(
          "containerPath",
          containerPath,
          vscode.ConfigurationTarget.Global
        );
      }

      vscode.window.showInformationMessage("Agent Zero configuration updated!");

      // Trigger model refresh
      provider.refreshModels();
    }
  );

  context.subscriptions.push(configureCommand);
}

export function deactivate() {
  console.log("Agent Zero Provider deactivated");
}

