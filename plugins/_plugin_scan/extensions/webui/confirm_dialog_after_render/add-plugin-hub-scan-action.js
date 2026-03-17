import { store as pluginScanStore } from "../../../webui/plugin-scan-store.js";

const NOTE_CLASS = "confirm-dialog-extension-note";
const BUTTON_CLASS = "confirm-dialog-plugin-scan-button";
const DIALOG_CLOSE_DELAY_MS = 220;

function isPluginHubInstallWarning(extensionContext) {
  return (
    extensionContext?.kind === "plugin_hub_plugin_install_warning"
    && extensionContext?.source === "plugin_installer"
    && typeof extensionContext?.gitUrl === "string"
    && extensionContext.gitUrl.trim().length > 0
  );
}

export default async function addPluginHubScanAction(context) {
  const extensionContext = context?.extensionContext;
  if (!isPluginHubInstallWarning(extensionContext)) return;

  const bodyElement = context?.bodyElement;
  const footerElement = context?.footerElement;
  const cancelButton = context?.cancelButton;
  if (!bodyElement || !footerElement || !cancelButton) return;

  if (!bodyElement.querySelector(`.${NOTE_CLASS}`)) {
    const note = document.createElement("p");
    note.className = NOTE_CLASS;
    note.textContent = "A0 Plugin Scanner can identify most threats. It is always recommended to scan all plugins and updates with A0 itself.";
    bodyElement.appendChild(note);
  }

  if (footerElement.querySelector(`.${BUTTON_CLASS}`)) return;

  const scanButton = document.createElement("button");
  scanButton.type = "button";
  scanButton.className = `button ${BUTTON_CLASS}`;
  scanButton.textContent = "Scan with A0";
  scanButton.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    context.close(false);
    window.setTimeout(() => {
      void pluginScanStore.openModal(extensionContext.gitUrl.trim());
    }, DIALOG_CLOSE_DELAY_MS);
  });

  footerElement.insertBefore(scanButton, cancelButton);
}
