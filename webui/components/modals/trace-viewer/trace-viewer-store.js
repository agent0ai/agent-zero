import { createStore } from "/js/AlpineStore.js";

let mermaidLoaded = false;
let mermaidModule = null;

async function ensureMermaid() {
  if (mermaidLoaded) return mermaidModule;
  try {
    mermaidModule = await import(
      "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs"
    );
    mermaidModule.default.initialize({
      startOnLoad: false,
      theme: "dark",
      themeVariables: {
        darkMode: true,
        background: "#1e1e2e",
        primaryColor: "#89b4fa",
        primaryTextColor: "#cdd6f4",
        primaryBorderColor: "#585b70",
        lineColor: "#6c7086",
        secondaryColor: "#313244",
        tertiaryColor: "#45475a",
      },
    });
    mermaidLoaded = true;
    return mermaidModule;
  } catch (e) {
    console.warn("Failed to load mermaid:", e);
    return null;
  }
}

const model = {
  loading: false,
  error: "",
  traceId: "",
  traceUrl: "",
  trace: null,
  observations: [],
  tree: null,
  diagramMode: "tree", // "tree" or "sequence"
  diagramSvg: "",
  selectedObsId: null,
  _initialized: false,

  init() {
    if (this._initialized) return;
    this._initialized = true;
    // Check for pending trace request (set before modal opens)
    const pending = globalThis._pendingTrace;
    if (pending) {
      globalThis._pendingTrace = null;
      this.loadTrace(pending.id, pending.url);
    }
  },

  async loadTrace(traceId, traceUrl) {
    this.traceId = traceId;
    this.traceUrl = traceUrl;
    this.loading = true;
    this.error = "";
    this.trace = null;
    this.observations = [];
    this.tree = null;
    this.diagramSvg = "";
    this.selectedObsId = null;

    try {
      const resp = await globalThis.fetchApi("/langfuse_trace", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ trace_id: traceId }),
      });
      const data = await resp.json();

      if (!data.success) {
        this.error = data.error || "Failed to load trace";
        this.loading = false;
        return;
      }

      this.trace = data.trace;
      this.observations = data.observations;
      this.traceUrl = data.trace_url || traceUrl;
      this.tree = buildTree(data.observations);
      this.loading = false;

      await this.renderDiagram();
    } catch (e) {
      this.error = e.message || "Failed to load trace";
      this.loading = false;
    }
  },

  async renderDiagram() {
    if (!this.observations.length) return;

    const mermaid = await ensureMermaid();
    if (!mermaid) {
      this.diagramSvg = "";
      return;
    }

    const code =
      this.diagramMode === "sequence"
        ? generateSequenceDiagram(this.tree, this.observations)
        : generateTreeDiagram(this.tree, this.observations);

    try {
      const { svg } = await mermaid.default.render(
        "trace-mermaid-" + Date.now(),
        code,
      );
      this.diagramSvg = svg;
    } catch (e) {
      console.warn("Mermaid render failed:", e);
      this.diagramSvg = `<pre class="mermaid-error">${escapeHtml(code)}</pre>`;
    }
  },

  async switchDiagram(mode) {
    this.diagramMode = mode;
    await this.renderDiagram();
  },

  toggleObservation(obsId) {
    this.selectedObsId = this.selectedObsId === obsId ? null : obsId;
  },

  isSelected(obsId) {
    return this.selectedObsId === obsId;
  },

  openPromptLab(obsId) {
    const obs = this.getObservation(obsId);
    if (!obs) return;

    // Extract system prompt from observation input
    let systemPrompt = "";
    let userMessage = "";
    const input = obs.input;
    if (typeof input === "string") {
      systemPrompt = input;
    } else if (Array.isArray(input)) {
      // Common pattern: array of messages with role/content
      for (const msg of input) {
        if (msg?.role === "system") systemPrompt += (msg.content || "") + "\n";
        if (msg?.role === "user") userMessage += (msg.content || "") + "\n";
      }
    } else if (input && typeof input === "object") {
      systemPrompt = JSON.stringify(input, null, 2);
    }

    const response = typeof obs.output === "string" ? obs.output : JSON.stringify(obs.output || "", null, 2);

    // Set Prompt Lab data before opening modal
    const promptLabStore = window.Alpine?.store("promptLab");
    if (promptLabStore) {
      const chatsStore = window.Alpine?.store("chats");
      const contextId = chatsStore?.getSelectedChatId() || "";

      promptLabStore.open({
        systemPrompt: systemPrompt.trim(),
        response: response,
        model: obs.model || "",
        tokenCount: (obs.usage_details?.input || 0) + (obs.usage_details?.output || 0),
        cost: obs.calculated_total_cost || 0,
        userMessage: userMessage.trim(),
        contextId: contextId,
        logNo: null,
      });
    }

    globalThis.openModal("modals/prompt-lab/prompt-lab.html");
  },

  getObservation(obsId) {
    return this.observations.find((o) => o.id === obsId) || null;
  },

  formatContent(value) {
    if (value == null) return null;
    if (typeof value === "object") return JSON.stringify(value, null, 2);
    return String(value);
  },

  formatTimestamp(iso) {
    if (!iso) return "-";
    try {
      const d = new Date(iso);
      return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit", fractionalSecondDigits: 3 });
    } catch {
      return iso;
    }
  },

  cleanup() {
    this.trace = null;
    this.observations = [];
    this.tree = null;
    this.diagramSvg = "";
    this.error = "";
    this.traceId = "";
    this.traceUrl = "";
    this.selectedObsId = null;
  },

  formatDuration(obs) {
    if (obs.latency == null) return "-";
    if (obs.latency < 1) return `${Math.round(obs.latency * 1000)}ms`;
    return `${obs.latency.toFixed(2)}s`;
  },

  formatCost(obs) {
    const cost = obs.calculated_total_cost;
    if (cost == null || cost === 0) return "-";
    if (cost < 0.001) return `$${(cost * 1000).toFixed(3)}m`;
    return `$${cost.toFixed(4)}`;
  },

  formatTokens(obs) {
    const u = obs.usage_details || {};
    const input = u.input || 0;
    const output = u.output || 0;
    if (!input && !output) return "-";
    return `${input}→${output}`;
  },

  typeIcon(obs) {
    const icons = {
      GENERATION: "smart_toy",
      SPAN: "account_tree",
      EVENT: "bolt",
    };
    return icons[obs.type] || "circle";
  },

  typeClass(obs) {
    return `obs-${(obs.type || "span").toLowerCase()}`;
  },
};

function buildTree(observations) {
  const byId = {};
  const roots = [];

  for (const obs of observations) {
    byId[obs.id] = { ...obs, children: [] };
  }

  for (const obs of observations) {
    const node = byId[obs.id];
    if (obs.parent_observation_id && byId[obs.parent_observation_id]) {
      byId[obs.parent_observation_id].children.push(node);
    } else {
      roots.push(node);
    }
  }

  // Sort children by start_time
  for (const node of Object.values(byId)) {
    node.children.sort(
      (a, b) => new Date(a.start_time || 0) - new Date(b.start_time || 0),
    );
  }

  return roots;
}

function generateTreeDiagram(tree, observations) {
  if (!tree || tree.length === 0) {
    return "graph TD\n    EMPTY[No trace observations]";
  }
  let lines = ["graph TD"];
  let counter = 0;

  function addNode(node, parentKey) {
    const key = `N${counter++}`;
    const label = sanitizeMermaid(
      `${node.name}${node.model ? " (" + node.model + ")" : ""}`,
    );
    const shape = node.type === "GENERATION" ? `([${label}])` : `[${label}]`;
    lines.push(`    ${key}${shape}`);
    if (parentKey) {
      const dur = node.latency != null ? `${node.latency.toFixed(1)}s` : "";
      lines.push(
        dur ? `    ${parentKey} -->|${dur}| ${key}` : `    ${parentKey} --> ${key}`,
      );
    }
    for (const child of node.children || []) {
      addNode(child, key);
    }
  }

  for (const root of tree || []) {
    addNode(root, null);
  }

  return lines.join("\n");
}

function generateSequenceDiagram(tree, observations) {
  if (!tree || tree.length === 0) {
    return "sequenceDiagram\n    Note right of System: No trace observations";
  }
  let lines = ["sequenceDiagram"];

  function getParticipant(node) {
    return sanitizeMermaid(node.name || "unknown").replace(/\s+/g, "_");
  }

  // Collect unique participants in order
  const participants = [];
  const seen = new Set();
  function collectParticipants(nodes) {
    for (const node of nodes || []) {
      const p = getParticipant(node);
      if (!seen.has(p)) {
        seen.add(p);
        participants.push({ key: p, label: node.name || "unknown" });
      }
      collectParticipants(node.children);
    }
  }
  collectParticipants(tree);

  for (const p of participants) {
    lines.push(`    participant ${p.key} as ${sanitizeMermaid(p.label)}`);
  }

  function addInteractions(nodes, parentParticipant) {
    for (const node of nodes || []) {
      const p = getParticipant(node);
      const dur = node.latency != null ? ` (${node.latency.toFixed(1)}s)` : "";
      const tokens = formatTokensShort(node);
      const note = tokens ? tokens + dur : dur.trim();

      if (parentParticipant && parentParticipant !== p) {
        lines.push(`    ${parentParticipant}->>+${p}: ${sanitizeMermaid(node.name || "call")}`)
        if (node.children?.length) {
          addInteractions(node.children, p);
        }
        lines.push(`    ${p}-->>-${parentParticipant}: ${note || "done"}`);
      } else if (node.children?.length) {
        addInteractions(node.children, p);
      }
    }
  }

  if (tree?.length) {
    const rootP = getParticipant(tree[0]);
    for (const root of tree) {
      addInteractions(root.children, getParticipant(root));
    }
  }

  return lines.join("\n");
}

function formatTokensShort(obs) {
  const u = obs.usage_details || {};
  const input = u.input || 0;
  const output = u.output || 0;
  if (!input && !output) return "";
  return `${input}+${output}tok`;
}

function sanitizeMermaid(str) {
  return (str || "")
    .replace(/[[\]{}()|#&;`"]/g, "")
    .replace(/-->/g, "->")
    .substring(0, 50);
}

function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

export const store = createStore("traceViewer", model);
