/**
 * OrchestrationCanvas — React Flow root component.
 *
 * Loaded dynamically from the orchestrator modal. Uses htm + React (no build step).
 * Communicates with Alpine via custom DOM events on #react-flow-root.
 */

export async function mountCanvas(rootEl) {
  // Dynamic imports from esm.sh CDN
  // Note: esm.sh bundles react internally when no ?external flag is used.
  // We use ?deps= to pin the React version so all packages share the same instance.
  const depsSuffix = "?deps=react@18.3.1,react-dom@18.3.1";

  const React = await import("https://esm.sh/react@18.3.1");
  const ReactDOM = await import("https://esm.sh/react-dom@18.3.1/client");
  const xyflow = await import(`https://esm.sh/@xyflow/react@12.6.0${depsSuffix}`);
  const {
    ReactFlow: ReactFlowComponent,
    ReactFlowProvider,
    useNodesState,
    useEdgesState,
    useReactFlow,
    addEdge,
    Background,
    Controls,
    MiniMap,
    Panel,
    Handle,
  } = xyflow;
  const htm = (await import("https://esm.sh/htm@3.1.1")).default;

  const html = htm.bind(React.createElement);
  const { useState, useCallback, useEffect, useRef, memo } = React;

  // Import CSS for React Flow (avoid duplicates on re-open)
  if (!document.querySelector('link[href*="xyflow/react"]')) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = "https://esm.sh/@xyflow/react@12.6.0/dist/style.css";
    document.head.appendChild(link);
  }

  // ─── Custom Node Components ───

  const InputNode = memo(({ data, selected }) => {
    return html`
      <div class="orch-node orch-node-input ${selected ? "selected" : ""} ${data._status || ""}">
        <div class="orch-node-badge">INPUT</div>
        <div class="orch-node-label">${data.label || "User Prompt"}</div>
        <div class="orch-node-detail">${data.promptMode === "fixed" ? "Fixed prompt" : "Runtime prompt"}</div>
        <${Handle} type="source" position="bottom" />
      </div>
    `;
  });

  const OutputNode = memo(({ data, selected }) => {
    return html`
      <div class="orch-node orch-node-output ${selected ? "selected" : ""} ${data._status || ""}">
        <${Handle} type="target" position="top" />
        <div class="orch-node-badge">OUTPUT</div>
        <div class="orch-node-label">${data.label || "Final Response"}</div>
        <div class="orch-node-detail">${data.format || "markdown"}</div>
      </div>
    `;
  });

  const AgentNode = memo(({ data, selected }) => {
    return html`
      <div class="orch-node orch-node-agent ${selected ? "selected" : ""} ${data._status || ""}">
        <${Handle} type="target" position="top" />
        <div class="orch-node-badge">AGENT</div>
        <div class="orch-node-label">${data.label || "Agent"}</div>
        <div class="orch-node-detail">${data.agentProfile || "default"}</div>
        ${data._status === "running" ? html`<div class="orch-node-spinner"></div>` : null}
        <${Handle} type="source" position="bottom" />
      </div>
    `;
  });

  const ParallelGroupNode = memo(({ data, selected }) => {
    return html`
      <div class="orch-node orch-node-parallel ${selected ? "selected" : ""} ${data._status || ""}">
        <${Handle} type="target" position="top" />
        <div class="orch-node-badge">PARALLEL</div>
        <div class="orch-node-label">${data.label || "Parallel Group"}</div>
        <div class="orch-node-detail">Merge: ${data.mergeStrategy || "concatenate"}</div>
        <${Handle} type="source" position="bottom" />
      </div>
    `;
  });

  const ConditionNode = memo(({ data, selected }) => {
    return html`
      <div class="orch-node orch-node-condition ${selected ? "selected" : ""} ${data._status || ""}">
        <${Handle} type="target" position="top" />
        <div class="orch-node-badge">CONDITION</div>
        <div class="orch-node-label">${data.label || "Condition"}</div>
        <div class="orch-node-detail">${data.expression ? "Has expression" : "No expression"}</div>
        <div class="orch-condition-handles">
          <${Handle} type="source" position="bottom" id="true" style=${{ left: "30%" }} />
          <${Handle} type="source" position="bottom" id="false" style=${{ left: "70%" }} />
        </div>
        <div class="orch-condition-labels">
          <span class="orch-cond-true">${data.trueLabel || "True"}</span>
          <span class="orch-cond-false">${data.falseLabel || "False"}</span>
        </div>
      </div>
    `;
  });

  // Node types must be defined outside the component
  const nodeTypes = {
    inputNode: InputNode,
    outputNode: OutputNode,
    agentNode: AgentNode,
    parallelGroupNode: ParallelGroupNode,
    conditionNode: ConditionNode,
  };

  // ─── Connection validation ───

  function hasCycle(nodes, edges, newEdge) {
    const adj = {};
    for (const e of edges) {
      if (!adj[e.source]) adj[e.source] = [];
      adj[e.source].push(e.target);
    }
    if (!adj[newEdge.source]) adj[newEdge.source] = [];
    adj[newEdge.source].push(newEdge.target);

    const visited = new Set();
    const stack = new Set();

    function dfs(node) {
      if (stack.has(node)) return true;
      if (visited.has(node)) return false;
      visited.add(node);
      stack.add(node);
      for (const neighbor of adj[node] || []) {
        if (dfs(neighbor)) return true;
      }
      stack.delete(node);
      return false;
    }

    return dfs(newEdge.source);
  }

  // ─── Main Flow Component ───

  function FlowCanvas() {
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const reactFlow = useReactFlow();
    const rootRef = useRef(null);

    // Connection handler with validation
    const onConnect = useCallback(
      (params) => {
        // Find source and target nodes
        const sourceNode = nodes.find((n) => n.id === params.source);
        const targetNode = nodes.find((n) => n.id === params.target);

        if (!sourceNode || !targetNode) return;

        // Input nodes: only source (no incoming)
        if (targetNode.type === "inputNode") return;
        // Output nodes: only target (no outgoing)
        if (sourceNode.type === "outputNode") return;
        // No self-connections
        if (params.source === params.target) return;
        // Cycle check
        if (hasCycle(nodes, edges, { source: params.source, target: params.target })) return;

        setEdges((eds) => addEdge({ ...params, animated: false }, eds));
      },
      [nodes, edges, setEdges]
    );

    // Notify Alpine of changes
    const onChangeTimeout = useRef(null);
    useEffect(() => {
      if (onChangeTimeout.current) clearTimeout(onChangeTimeout.current);
      onChangeTimeout.current = setTimeout(() => {
        const root = document.getElementById("react-flow-root");
        if (root) {
          root.dispatchEvent(
            new CustomEvent("flow:changed", {
              detail: {
                nodes: nodes.map((n) => ({ ...n, data: { ...n.data, _status: undefined } })),
                edges,
              },
            })
          );
        }
      }, 300);
    }, [nodes, edges]);

    // Notify Alpine of node selection
    const onNodeClick = useCallback((event, node) => {
      const root = document.getElementById("react-flow-root");
      if (root) {
        root.dispatchEvent(
          new CustomEvent("flow:nodeSelect", {
            detail: { nodeId: node.id, data: node.data },
          })
        );
      }
    }, []);

    const onPaneClick = useCallback(() => {
      const root = document.getElementById("react-flow-root");
      if (root) {
        root.dispatchEvent(
          new CustomEvent("flow:nodeSelect", { detail: { nodeId: null, data: null } })
        );
      }
    }, []);

    // Listen for Alpine → React events
    useEffect(() => {
      const root = document.getElementById("react-flow-root");
      if (!root) return;

      const onLoad = (e) => {
        const { nodes: n, edges: ed, viewport: vp } = e.detail;
        setNodes(n || []);
        setEdges(ed || []);
        if (vp) {
          setTimeout(() => reactFlow.setViewport(vp), 100);
        }
      };

      const onReset = () => {
        setNodes([]);
        setEdges([]);
      };

      const onNodeStates = (e) => {
        const states = e.detail;
        setNodes((nds) =>
          nds.map((n) => {
            const st = states[n.id];
            if (st) {
              return { ...n, data: { ...n.data, _status: st.status } };
            }
            return n;
          })
        );
      };

      const onUpdateNode = (e) => {
        const { nodeId, data } = e.detail;
        setNodes((nds) =>
          nds.map((n) => {
            if (n.id === nodeId) {
              return { ...n, data: { ...n.data, ...data } };
            }
            return n;
          })
        );
      };

      root.addEventListener("flow:load", onLoad);
      root.addEventListener("flow:reset", onReset);
      root.addEventListener("flow:nodeStates", onNodeStates);
      root.addEventListener("flow:updateNode", onUpdateNode);

      // Signal React is ready
      root.dispatchEvent(new CustomEvent("flow:reactReady"));

      return () => {
        root.removeEventListener("flow:load", onLoad);
        root.removeEventListener("flow:reset", onReset);
        root.removeEventListener("flow:nodeStates", onNodeStates);
        root.removeEventListener("flow:updateNode", onUpdateNode);
      };
    }, [setNodes, setEdges, reactFlow]);

    // Drag and drop from palette
    const onDragOver = useCallback((event) => {
      event.preventDefault();
      event.dataTransfer.dropEffect = "move";
    }, []);

    const onDrop = useCallback(
      (event) => {
        event.preventDefault();
        const type = event.dataTransfer.getData("application/reactflow-type");
        if (!type) return;

        const position = reactFlow.screenToFlowPosition({
          x: event.clientX,
          y: event.clientY,
        });

        const id = `${type}-${Date.now()}`;
        const defaults = {
          agentNode: { label: "Agent", agentProfile: "default", systemPromptOverride: "", model: "", tools: [], outputVariable: "" },
          parallelGroupNode: { label: "Parallel Group", mergeStrategy: "concatenate" },
          conditionNode: { label: "Condition", expression: "", trueLabel: "True", falseLabel: "False" },
          inputNode: { label: "User Prompt", promptMode: "runtime", fixedPrompt: "" },
          outputNode: { label: "Final Response", format: "markdown" },
        };

        const newNode = {
          id,
          type,
          position,
          data: defaults[type] || { label: type },
        };

        setNodes((nds) => nds.concat(newNode));
      },
      [reactFlow, setNodes]
    );

    return html`
      <div style=${{ width: "100%", height: "100%" }} ref=${rootRef}>
        <${ReactFlowComponent}
          nodes=${nodes}
          edges=${edges}
          onNodesChange=${onNodesChange}
          onEdgesChange=${onEdgesChange}
          onConnect=${onConnect}
          onNodeClick=${onNodeClick}
          onPaneClick=${onPaneClick}
          onDragOver=${onDragOver}
          onDrop=${onDrop}
          nodeTypes=${nodeTypes}
          fitView
          snapToGrid=${true}
          snapGrid=${[15, 15]}
          deleteKeyCode="Delete"
          style=${{ background: "var(--color-background, #1a1a2e)" }}
        >
          <${Background} variant="dots" gap=${20} size=${1} color="rgba(255,255,255,0.05)" />
          <${Controls} position="bottom-right" />
          <${MiniMap}
            position="bottom-left"
            style=${{ background: "rgba(0,0,0,0.3)" }}
            maskColor="rgba(0,0,0,0.5)"
          />
          <${NodePalette} html=${html} />
        </${ReactFlowComponent}>
      </div>
    `;
  }

  // ─── Node Palette ───

  function NodePalette({ html: h }) {
    const onDragStart = (event, nodeType) => {
      event.dataTransfer.setData("application/reactflow-type", nodeType);
      event.dataTransfer.effectAllowed = "move";
    };

    const items = [
      { type: "inputNode", label: "Input", icon: "arrow_downward", color: "#4ade80" },
      { type: "agentNode", label: "Agent", icon: "smart_toy", color: "#60a5fa" },
      { type: "parallelGroupNode", label: "Parallel", icon: "call_split", color: "#c084fc" },
      { type: "conditionNode", label: "Condition", icon: "call_split", color: "#fbbf24" },
      { type: "outputNode", label: "Output", icon: "arrow_upward", color: "#f87171" },
    ];

    return h`
      <${Panel} position="top-left">
        <div class="orch-palette">
          <div class="orch-palette-title">Nodes</div>
          ${items.map(
            (item) => h`
              <div
                key=${item.type}
                class="orch-palette-item"
                draggable="true"
                onDragStart=${(e) => onDragStart(e, item.type)}
                style=${{ borderLeftColor: item.color }}
              >
                <span class="material-symbols-outlined" style=${{ color: item.color, fontSize: "18px" }}>${item.icon}</span>
                <span>${item.label}</span>
              </div>
            `
          )}
        </div>
      </${Panel}>
    `;
  }

  // ─── Mount ───

  function App() {
    return html`
      <${ReactFlowProvider}>
        <${FlowCanvas} />
      </${ReactFlowProvider}>
    `;
  }

  const root = ReactDOM.createRoot(rootEl);
  root.render(html`<${App} />`);

  return () => root.unmount();
}
