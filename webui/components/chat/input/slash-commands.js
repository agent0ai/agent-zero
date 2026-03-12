import { createStore } from "/js/AlpineStore.js";

const COMMANDS = [
  {
    command: "/skill-install",
    description: "Install skills from GitHub (skills.sh)",
    usage: "/skill-install owner/repo[/skill-name]",
  },
  {
    command: "/skill-list",
    description: "Show installed skills",
    usage: "/skill-list",
  },
  {
    command: "/skill-remove",
    description: "Remove an installed skill",
    usage: "/skill-remove <skill-path>",
  },
];

const model = {
  visible: false,
  commands: [],
  selectedIndex: 0,

  onInput(value) {
    if (!value.startsWith("/")) {
      this.hide();
      return;
    }

    const hasSpace = value.includes(" ");
    const typed = value.split(/\s/)[0].toLowerCase();

    if (hasSpace) {
      this.hide();
      return;
    }

    this.commands = COMMANDS.filter((c) =>
      c.command.startsWith(typed)
    );

    if (this.commands.length === 0) {
      this.hide();
      return;
    }

    this.selectedIndex = 0;
    this.visible = true;
  },

  hide() {
    this.visible = false;
    this.commands = [];
    this.selectedIndex = 0;
  },

  selectCommand(index) {
    const cmd = this.commands[index];
    if (!cmd) return;

    const input = document.getElementById("chat-input");
    if (!input) return;

    const store = globalThis.Alpine?.store("chatInput");
    if (store) {
      store.message = cmd.command + " ";
    } else {
      input.value = cmd.command + " ";
    }

    this.hide();
    input.focus();
  },

  onKeydown(event) {
    if (!this.visible) return false;

    switch (event.key) {
      case "ArrowUp":
        event.preventDefault();
        this.selectedIndex = Math.max(0, this.selectedIndex - 1);
        return true;

      case "ArrowDown":
        event.preventDefault();
        this.selectedIndex = Math.min(
          this.commands.length - 1,
          this.selectedIndex + 1
        );
        return true;

      case "Tab":
      case "Enter":
        if (this.commands.length > 0) {
          event.preventDefault();
          event.stopPropagation();
          this.selectCommand(this.selectedIndex);
          return true;
        }
        return false;

      case "Escape":
        event.preventDefault();
        this.hide();
        return true;

      default:
        return false;
    }
  },
};

const store = createStore("slashCommands", model);

export { store, COMMANDS };
