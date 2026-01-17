### diagram_tool:
Generate visual diagrams using Mermaid, Excalidraw, or Draw.io
Create flowcharts, sequence diagrams, architecture diagrams, network diagrams, and more
Output to files or inline rendering in chat

**Diagram types supported:**
- **mermaid**: Flowcharts, sequence, class, state, ER, Gantt, pie charts, git graphs
- **excalidraw**: Hand-drawn style diagrams, sketches, architecture visuals
- **drawio**: Professional technical diagrams, network topology, enterprise architecture

**Usage:**

1. **Mermaid Inline (Recommended for chat)**

Use this for most diagrams - they render beautifully in the chat:

~~~json
{
    "thoughts": [
        "User wants a flowchart",
        "I'll use Mermaid inline rendering",
    ],
    "headline": "Creating flowchart diagram",
    "tool_name": "response",
    "tool_args": {
        "text": "Here's the process flow:\n\n```mermaid\ngraph TD\n    A[Start] --> B{Decision}\n    B -->|Yes| C[Process]\n    B -->|No| D[End]\n    C --> D\n```"
    }
}
~~~

2. **Mermaid to File (For saving/exporting)**

~~~json
{
    "thoughts": [
        "User wants to save diagram as PNG",
        "I'll use diagram_tool to export",
    ],
    "headline": "Generating Mermaid diagram file",
    "tool_name": "diagram_tool",
    "tool_args": {
        "diagram_type": "mermaid",
        "code": "sequenceDiagram\n    User->>Agent: Request\n    Agent->>Tool: Execute\n    Tool-->>Agent: Result\n    Agent-->>User: Response",
        "output_path": "/tmp/sequence_diagram.png",
        "format": "png",
        "theme": "default"
    }
}
~~~

3. **Excalidraw Diagram**

~~~json
{
    "thoughts": [
        "User wants hand-drawn style architecture",
        "Excalidraw template works well",
    ],
    "headline": "Creating Excalidraw architecture diagram",
    "tool_name": "diagram_tool",
    "tool_args": {
        "diagram_type": "excalidraw",
        "template": "flowchart",
        "output_path": "/tmp/architecture.excalidraw",
        "format": "json"
    }
}
~~~

4. **Draw.io Diagram**

~~~json
{
    "thoughts": [
        "User needs professional network diagram",
        "Draw.io network template is perfect",
    ],
    "headline": "Creating network topology diagram",
    "tool_name": "diagram_tool",
    "tool_args": {
        "diagram_type": "drawio",
        "template": "network",
        "output_path": "/tmp/network.png",
        "format": "png"
    }
}
~~~

**Mermaid Diagram Examples:**

Flowchart:
```mermaid
flowchart LR
    A[Start] --> B{Check}
    B -->|Pass| C[Continue]
    B -->|Fail| D[Error]
    C --> E[End]
```

Sequence Diagram:
```mermaid
sequenceDiagram
    participant User
    participant Agent
    participant Tool
    User->>Agent: Request task
    Agent->>Tool: Execute
    Tool-->>Agent: Result
    Agent-->>User: Response
```

Class Diagram:
```mermaid
classDiagram
    class Tool {
        +execute()
        +before_execution()
        +after_execution()
    }
    class DiagramTool {
        +generate_diagram()
    }
    Tool <|-- DiagramTool
```

State Diagram:
```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Processing: Start
    Processing --> Success: Complete
    Processing --> Error: Fail
    Success --> [*]
    Error --> Idle: Retry
```

ER Diagram:
```mermaid
erDiagram
    USER ||--o{ ORDER : places
    ORDER ||--|{ LINE-ITEM : contains
    PRODUCT ||--o{ LINE-ITEM : "ordered in"
```

Gantt Chart:
```mermaid
gantt
    title Project Timeline
    dateFormat YYYY-MM-DD
    section Phase 1
    Task 1: 2026-01-01, 30d
    Task 2: 2026-02-01, 20d
    section Phase 2
    Task 3: 2026-02-15, 25d
```

Pie Chart:
```mermaid
pie title Resource Distribution
    "CPU" : 45
    "Memory" : 30
    "Storage" : 15
    "Network" : 10
```

Git Graph:
```mermaid
gitGraph
    commit
    branch develop
    commit
    commit
    checkout main
    merge develop
    commit
```

**Arguments:**
- diagram_type: "mermaid" | "excalidraw" | "drawio"
- code: Mermaid syntax (for mermaid type)
- elements: Array of elements (for excalidraw type)
- xml: Draw.io XML (for drawio type)
- template: Predefined template name (optional)
- output_path: File path to save (required for file output)
- format: "png" | "svg" | "pdf" | "json" | "xml"
- theme: "default" | "dark" | "forest" | "neutral" (mermaid only)

**Best Practices:**
1. Use Mermaid inline rendering for chat responses (easiest for users)
2. Use diagram_tool for file exports when user needs to save/share
3. For quick diagrams: Mermaid
4. For beautiful hand-drawn: Excalidraw
5. For professional technical: Draw.io
6. Always provide full file paths in output
7. Show diagram syntax in code blocks for user reference
