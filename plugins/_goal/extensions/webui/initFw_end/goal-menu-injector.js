import { store as chatInputStore } from "/components/chat/input/input-store.js";

const MENU_SELECTOR = ".chat-bottom-actions-menu";
const BUTTON_ID = "goal-chat-more-item";

function buildButton() {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "chat-bottom-menu-item";
  button.id = BUTTON_ID;
  button.innerHTML = `
    <x-icon aria-hidden="true" name="track_changes"></x-icon>
    <span>Goal mode</span>
  `;

  button.addEventListener("click", () => {
    chatInputStore.closeChatMoreMenu();
    chatInputStore.message = "/goal ";
    chatInputStore.adjustTextareaHeight();
    chatInputStore.focus();
    chatInputStore._setEditorCaret?.(chatInputStore.message.length);
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

export default async function initGoalMenuInjector() {
  scan();

  const observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      for (const node of mutation.addedNodes) {
        if (!(node instanceof Element)) continue;

        if (node.matches?.(MENU_SELECTOR)) {
          injectButton(node);
          continue;
        }

        if (node.querySelectorAll) scan(node);
      }
    }
  });

  observer.observe(document.body, {
    childList: true,
    subtree: true,
  });
}
