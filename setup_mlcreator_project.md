# Agent Zero Setup Plan for MLcreator Project

## 🎯 Objective
Configure Agent Zero as the primary development assistant and project manager for the MLcreator Unity project, with proper memory, knowledge base, and workflow integration.

## 📋 Project Overview
- **Project Path**: `D:\GithubRepos\MLcreator`
- **Type**: Unity 3D project with Game Creator modules
- **Technologies**: Unity, C#, Python, MCP servers, ML-Agents
- **Environment**: Windows with multiple activation scripts

## 🗂️ Agent Zero Folder Structure Setup

### 1. Memory Structure (`/memory/mlcreator/`)
```
agent-zero/
├── memory/
│   └── mlcreator/                    # Project-specific memory
│       ├── db/                        # Vector database
│       │   ├── index.faiss
│       │   ├── index.pkl
│       │   ├── embedding.json
│       │   └── knowledge_import.json
│       └── embeddings/                # Cached embeddings
```

### 2. Knowledge Base Structure (`/knowledge/mlcreator/`)
```
agent-zero/
├── knowledge/
│   └── mlcreator/                     # Project knowledge base
│       ├── main/                      # General project knowledge
│       │   ├── project_overview.md
│       │   ├── architecture.md
│       │   ├── dependencies.md
│       │   └── conventions.md
│       ├── fragments/                 # Work-in-progress
│       │   ├── current_tasks.md
│       │   └── issues.md
│       ├── solutions/                 # Solved problems
│       │   ├── unity_patterns.md
│       │   ├── gamecreator_solutions.md
│       │   ├── mcp_integrations.md
│       │   └── ml_training_configs.md
│       └── instruments/               # Tool documentation
│           ├── activation_scripts.md
│           ├── mcp_servers.md
│           └── development_tools.md
```

### 3. Prompts Structure (`/prompts/mlcreator/`)
```
agent-zero/
├── prompts/
│   └── mlcreator/                    # Project-specific prompts
│       ├── agent.system.md           # Main system prompt
│       ├── tools.md                  # Tool usage instructions
│       ├── coding_standards.md       # C# and Unity conventions
│       └── workflow.md               # Development workflow
```

### 4. Instruments (`/instruments/mlcreator/`)
```
agent-zero/
├── instruments/
│   └── mlcreator/                    # Project tools
│       ├── unity_build.py            # Unity build automation
│       ├── gamecreator_tools.py      # Game Creator utilities
│       ├── ml_training.py            # ML-Agents training
│       └── environment_manager.py    # Environment activation
```

## 📝 Configuration Files

### 1. Project Configuration (`.env` additions)
```env
# MLcreator Project Settings
MEMORY_SUBDIR=mlcreator
KNOWLEDGE_SUBDIRS=mlcreator
PROJECT_PATH=D:\GithubRepos\MLcreator
UNITY_VERSION=2022.3.16f1
PYTHON_VERSION=3.10.11

# Auto-recall for Unity development
MEMORY_AUTO_RECALL=true
MEMORY_AUTO_RECALL_DELAYED=false
MEMORY_AUTO_RECALL_QUERY_PREP=true
MEMORY_AUTO_RECALL_POST_FILTER=true
MEMORY_AUTO_RECALL_INTERVAL=3
MEMORY_AUTO_RECALL_HISTORY_LENGTH=15000
MEMORY_THRESHOLD=0.75
MEMORY_LIMIT=15
```

### 2. CLAUDE.md (Agent Zero Integration)
```markdown
# MLcreator Project Instructions for Agent Zero

## Project Context
You are managing a Unity 3D project with Game Creator modules, ML-Agents, and multiple MCP server integrations.

## Key Responsibilities
1. Unity development with Game Creator framework
2. Python environment management (multiple versions)
3. MCP server orchestration
4. ML-Agents training and integration
5. Cross-platform development (Windows primary)

## Project Structure
- **Assets/**: Unity game assets and scenes
- **ML_AgentsConfig/**: ML training configurations
- **scripts/**: Automation and utility scripts
- **docs/**: Project documentation
- **claudedocs/**: AI-generated documentation

## Critical Files
- `activate-*.ps1`: Environment activation scripts
- `*.csproj`: Unity project files
- `pyrightconfig.json`: Python configuration
- `claude-code-mcp-config.json`: MCP configuration

## Development Workflow
1. Always check current environment before operations
2. Use appropriate activation script for context
3. Maintain Game Creator module compatibility
4. Follow Unity C# conventions
5. Document all AI-assisted changes

## Memory Areas Usage
- **main**: Project architecture and conventions
- **fragments**: Current development tasks
- **solutions**: Resolved Unity/Game Creator issues
- **instruments**: Tool and script documentation
```

### 3. AGENTS.md (Workflow Rules)
```markdown
# Agent Zero Workflow Rules for MLcreator

## Agent Hierarchy
```
Agent 0 (Project Manager)
├── Agent 1 (Unity Developer)
│   ├── Agent 1.1 (Game Creator Specialist)
│   └── Agent 1.2 (ML-Agents Trainer)
├── Agent 2 (Environment Manager)
│   ├── Agent 2.1 (Python Environment)
│   └── Agent 2.2 (MCP Server Manager)
└── Agent 3 (Documentation)
    ├── Agent 3.1 (Code Documentation)
    └── Agent 3.2 (Knowledge Base)
```

## Workflow Phases

### 1. Initialization Phase
- Load project memory from `mlcreator` subdirectory
- Check Unity and Python environments
- Verify MCP server configurations
- Load recent task context

### 2. Development Phase
- **Before Changes**:
  - Search memory for similar solutions
  - Check Unity version compatibility
  - Verify Game Creator module dependencies

- **During Development**:
  - Auto-recall relevant patterns every 3 messages
  - Consolidate duplicate solutions
  - Track all code modifications

- **After Changes**:
  - Update memory with new solutions
  - Document in appropriate knowledge area
  - Run Unity tests if applicable

### 3. Environment Management
- **Python Environments**:
  - serena-env: Serena MCP server
  - ML-Agents: Unity ML training
  - Global tools: Development utilities

- **Activation Scripts**:
  - `activate-ai.ps1`: AI development environment
  - `activate-unity.ps1`: Unity development
  - `activate-devops.ps1`: CI/CD operations
  - `activate-web.ps1`: Web services

### 4. Memory Management Rules
- **Save Patterns**:
  ```python
  # Unity patterns → solutions area
  memory_save(text=unity_solution, area="solutions",
              tags=["unity", "gamecreator"])

  # Current work → fragments area
  memory_save(text=wip_code, area="fragments",
              tags=["wip", "current"])

  # Architecture → main area
  memory_save(text=design_decision, area="main",
              tags=["architecture", "decision"])
  ```

- **Search Patterns**:
  ```python
  # Search for Game Creator solutions
  memory_load(query="Game Creator module",
              threshold=0.8, area="solutions")

  # Find Unity patterns
  memory_load(query="Unity pattern singleton",
              threshold=0.75, filter='tags contains "unity"')
  ```

## Task Delegation Rules

### Unity Development Tasks
- Delegate to Agent 1 for C# coding
- Use Agent 1.1 for Game Creator specifics
- Use Agent 1.2 for ML training setup

### Environment Tasks
- Delegate to Agent 2 for environment issues
- Use Agent 2.1 for Python dependencies
- Use Agent 2.2 for MCP server management

### Documentation Tasks
- Delegate to Agent 3 for documentation
- Auto-generate docs in `claudedocs/`
- Update knowledge base regularly

## Quality Gates

### Before Committing Code
1. Check Unity console for errors
2. Verify Game Creator compatibility
3. Test ML-Agent configurations
4. Update relevant memories

### Memory Consolidation Triggers
- Similar Unity errors (threshold: 0.85)
- Duplicate Game Creator patterns
- Repeated environment issues

### Knowledge Update Triggers
- New Unity patterns discovered
- Game Creator module updates
- ML training improvements
- Environment configuration changes

## Communication Protocols

### Status Reporting
```markdown
## Task: [Task Name]
**Agent**: [Agent ID]
**Status**: [In Progress/Completed/Blocked]
**Memory Updated**: [Yes/No]
**Knowledge Added**: [Yes/No]

### Changes Made:
- [List of changes]

### Issues Encountered:
- [List of issues]

### Solutions Applied:
- [Memory ID: solution_description]
```

### Error Handling
1. Search memory for similar errors
2. If no solution found, create new solution
3. Save solution with high importance
4. Update knowledge base

## Performance Optimizations

### Memory Settings
- Consolidation threshold: 0.85 (aggressive)
- Auto-recall: Every 3 messages
- Cache embeddings: Enabled
- Batch operations: When possible

### Search Optimization
- Unity queries: threshold=0.75
- Game Creator: threshold=0.80
- ML-Agents: threshold=0.70
- Use metadata filters for speed

## Integration Points

### With Unity Editor
- Monitor console output
- Track compilation times
- Cache frequently used assets

### With MCP Servers
- Maintain connection pool
- Monitor server health
- Auto-restart on failure

### With Version Control
- Auto-save memories before commits
- Tag memories with commit IDs
- Track solution evolution
```

## 🚀 Activation Procedure

### Phase 1: Initial Setup
```powershell
# 1. Navigate to Agent Zero directory
cd D:\GithubRepos\agent-zero

# 2. Create project directories
mkdir -p memory\mlcreator\db
mkdir -p memory\mlcreator\embeddings
mkdir -p knowledge\mlcreator\main
mkdir -p knowledge\mlcreator\fragments
mkdir -p knowledge\mlcreator\solutions
mkdir -p knowledge\mlcreator\instruments
mkdir -p prompts\mlcreator
mkdir -p instruments\mlcreator

# 3. Copy configuration files
copy setup_files\CLAUDE.md prompts\mlcreator\
copy setup_files\AGENTS.md prompts\mlcreator\
```

### Phase 2: Knowledge Population
```python
# Run from Agent Zero Python environment
python populate_mlcreator_knowledge.py
```

### Phase 3: Memory Initialization
```python
# Initialize memory with project context
python init_mlcreator_memory.py
```

### Phase 4: Agent Activation
1. Start Agent Zero with MLcreator configuration
2. Load project-specific prompts
3. Enable auto-recall
4. Initialize MCP connections

### Phase 5: Verification
```python
# Test memory and knowledge access
python verify_mlcreator_setup.py
```

## 📊 Success Criteria

### Setup Validation
- [ ] All directories created
- [ ] Configuration files in place
- [ ] Memory database initialized
- [ ] Knowledge files indexed
- [ ] Auto-recall functioning
- [ ] MCP servers accessible
- [ ] Unity project detected
- [ ] Python environments verified

### Operational Validation
- [ ] Can recall Unity patterns
- [ ] Can search Game Creator solutions
- [ ] Can delegate to sub-agents
- [ ] Memory consolidation working
- [ ] Knowledge updates successful

## 🔧 Maintenance Tasks

### Daily
- Consolidate duplicate memories
- Update fragment memories
- Clear old temporary data

### Weekly
- Review and organize solutions
- Update knowledge base
- Optimize memory indices

### Monthly
- Archive old memories
- Rebuild embeddings cache
- Performance analysis

## 📝 Notes

### Critical Paths
- Unity Editor: `C:\Program Files\Unity\Hub\Editor\2022.3.16f1\`
- Python: Multiple versions managed by pyenv
- MCP Servers: Various locations, check activation scripts

### Known Issues
- Python environment conflicts (use specific activation scripts)
- Unity compilation delays (cache frequently)
- MCP server timeouts (implement retry logic)

### Performance Tips
- Pre-load Game Creator patterns
- Cache Unity build outputs
- Batch memory operations
- Use project-specific embeddings