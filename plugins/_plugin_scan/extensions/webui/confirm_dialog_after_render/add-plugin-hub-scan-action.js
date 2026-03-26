import { store as pluginScanStore } from "../../../webui/plugin-scan-store.js";

const INSTALL_BUTTON_CLASS = "confirm-dialog-install-button";
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

  const footerElement = context?.footerElement;
  const confirmButton = context?.confirmButton;
  if (!footerElement || !confirmButton) return;

  if (footerElement.querySelector(`.${BUTTON_CLASS}`)) return;

  confirmButton.classList.remove("confirm");
  confirmButton.classList.add(INSTALL_BUTTON_CLASS);

  const scanButton = document.createElement("button");
  scanButton.type = "button";
  scanButton.className = `button confirm ${BUTTON_CLASS}`;
  scanButton.textContent = "Scan with Agent Zero";
  scanButton.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    context.close(false);
    window.setTimeout(() => {
      void pluginScanStore.openModal(extensionContext.gitUrl.trim());
    }, DIALOG_CLOSE_DELAY_MS);
  });

  footerElement.appendChild(scanButton);
}
