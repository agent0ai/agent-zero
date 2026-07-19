import { store as pluginSettingsStore } from "/components/plugins/plugin-settings-store.js";
import { store as chatInputStore } from "/components/chat/input/input-store.js";
import { store as chatsStore } from "/components/sidebar/chats/chats-store.js";

const MENU_SELECTOR = ".chat-bottom-actions-menu";
const BUTTON_ID = "skills-chat-more-item";

function buildButton() {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "chat-bottom-menu-item";
  button.id = BUTTON_ID;
  button.innerHTML = `
    <span class="material-symbols-outlined" aria-hidden="true">menu_book</span>
    <span>Skills</span>
  `;

  button.addEventListener("click", async () => {
    chatInputStore.closeChatMoreMenu();
    const projectName = chatsStore.selectedContext?.project?.name || "";
    await pluginSettingsStore.openConfig("_skills", projectName, "", { focus: "chat" });
  });

  return button;
}

function injectButton(menu) {
  if (!(menu instanceof HTMLElement)) return;
  if (menu.querySelector(`#${BUTTON_ID}`)) return;
  menu.appendChild(buildButton());
}

function scan(root = document) {
  for (const menu of root.querySelectorAll(MENU_SELECTOR)) {
    injectButton(menu);
  }
}

export default async function initSkillsMenuInjector() {
  scan();

  const observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      for (const node of mutation.addedNodes) {
        if (!(node instanceof Element)) continue;

        if (node.matches?.(MENU_SELECTOR)) {
          injectButton(node);
          continue;
        }

        if (node.querySelectorAll) {
          scan(node);
        }
      }
    }
  });

  observer.observe(document.body, {
    childList: true,
    subtree: true,
  });
}
