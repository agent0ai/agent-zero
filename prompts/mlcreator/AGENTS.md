# Agent Zero Workflow Rules for MLcreator Project

## 🤖 Agent Hierarchy and Responsibilities

```
Agent 0 (Project Orchestrator) - YOU
├── Agent 1 (Unity Development Lead)
│   ├── Agent 1.1 (Game Creator Specialist)
│   ├── Agent 1.2 (C# Code Optimizer)
│   └── Agent 1.3 (Unity Performance Analyst)
├── Agent 2 (ML & AI Systems)
│   ├── Agent 2.1 (ML-Agents Trainer)
│   ├── Agent 2.2 (Neural Network Optimizer)
│   └── Agent 2.3 (Behavior Designer)
├── Agent 3 (Environment & DevOps)
│   ├── Agent 3.1 (Python Environment Manager)
│   ├── Agent 3.2 (MCP Server Orchestrator)
│   └── Agent 3.3 (Build Pipeline Manager)
└── Agent 4 (Knowledge & Documentation)
    ├── Agent 4.1 (Code Documentor)
    ├── Agent 4.2 (Memory Curator)
    └── Agent 4.3 (Solution Archivist)
```

## 📋 Workflow Phases

### Phase 1: Initialization (Every Session Start)
```python
# Workflow sequence
1. Load project memory context
   memory = Memory.get_by_subdir("mlcreator")

2. Check environment status
   - Unity Editor version
   - Python environments
   - MCP server availability

3. Load recent work context
   fragments = memory_load(area="fragments", limit=5)

4. Review pending tasks
   tasks = memory_load(query="TODO pending", area="fragments")

5. Activate appropriate environment
   Run: ./activate-unity.ps1 or ./activate-ai.ps1
```

### Phase 2: Task Analysis
```python
# Decision tree for task delegation

if task.involves("Unity", "Game Creator", "C#"):
    delegate_to(Agent_1)
    if task.specific_to("Game Creator modules"):
        sub_delegate_to(Agent_1_1)
    elif task.requires("performance optimization"):
        sub_delegate_to(Agent_1_3)

elif task.involves("ML-Agents", "training", "AI"):
    delegate_to(Agent_2)
    if task.is("training configuration"):
        sub_delegate_to(Agent_2_1)
    elif task.is("behavior design"):
        sub_delegate_to(Agent_2_3)

elif task.involves("environment", "setup", "deployment"):
    delegate_to(Agent_3)

elif task.involves("documentation", "memory"):
    delegate_to(Agent_4)
```

### Phase 3: Development Execution

#### Pre-Development Checklist
- [ ] Search memory for similar problems
- [ ] Check Unity console for existing errors
- [ ] Verify Game Creator module versions
- [ ] Ensure correct environment activated
- [ ] Review relevant documentation

#### During Development Protocol
```python
# Every 3 messages (auto-recall trigger)
1. Auto-recall relevant memories
2. Check for pattern matches
3. Apply known solutions
4. Document new discoveries

# On encountering issues
if problem.is_new():
    1. Document problem in fragments
    2. Search for similar patterns
    3. Develop solution
    4. Test thoroughly
    5. Save to solutions area
else:
    1. Apply existing solution
    2. Verify effectiveness
    3. Update if needed
```

#### Post-Development Actions
```python
# Mandatory steps
1. memory_save(solution, area="solutions", importance="high")
2. Update fragments with progress
3. Run Unity play mode test
4. Check for new warnings/errors
5. Document in claudedocs/ if significant
6. Consolidate duplicate memories
```

## 🔄 Memory Management Workflow

### Memory Save Patterns
```python
# Unity Error Solution
memory_save(
    text=f"Unity Error: {error_type}\nContext: {context}\nSolution: {solution}",
    area="solutions",
    tags=["unity", "error", module_name],
    importance="high"
)

# Game Creator Pattern
memory_save(
    text=f"Game Creator Pattern: {pattern_name}\nModule: {module}\nImplementation: {code}",
    area="solutions",
    tags=["gamecreator", module, "pattern"],
    category="implementation"
)

# Work in Progress
memory_save(
    text=f"WIP: {task_description}\nProgress: {status}\nNext: {next_steps}",
    area="fragments",
    tags=["wip", "current", date.today()],
    ttl=604800  # 7 days
)

# Architecture Decision
memory_save(
    text=f"Architecture: {decision_title}\nRationale: {reasoning}\nImplementation: {details}",
    area="main",
    tags=["architecture", "decision", component],
    importance="critical"
)
```

### Memory Search Patterns
```python
# Find Unity solutions
solutions = memory_load(
    query="Unity {error_type} Game Creator",
    area="solutions",
    threshold=0.75,
    limit=10
)

# Get recent work
recent = memory_load(
    filter='area == "fragments" and timestamp > "{yesterday}"',
    limit=20
)

# Find specific patterns
patterns = memory_load(
    query="Game Creator {module} implementation",
    filter='tags contains "pattern"',
    threshold=0.8
)
```

### Memory Consolidation Rules
```python
# Consolidation triggers
if similarity > 0.85:
    if both_are_solutions:
        action = "MERGE"  # Combine into comprehensive solution
    elif one_is_fragment:
        action = "REPLACE"  # Fragment becomes solution
    else:
        action = "UPDATE"  # Enhance existing

# Weekly consolidation
Every Monday:
    1. Merge duplicate Unity errors
    2. Archive completed fragments
    3. Promote tested solutions
    4. Clean temporary memories
```

## 🎯 Task Delegation Protocols

### Unity Development (Agent 1)
```python
# Delegation criteria
delegate_when:
    - C# code writing/reviewing
    - Unity Editor operations
    - Game Creator customization
    - Performance optimization
    - Shader programming

# Return expectations
expects:
    - Compilable C# code
    - Unity best practices followed
    - Game Creator compatibility verified
    - Performance metrics included
    - Memory updated with patterns
```

### ML & AI Systems (Agent 2)
```python
# Delegation criteria
delegate_when:
    - ML-Agents configuration
    - Training hyperparameter tuning
    - Behavior tree design
    - Neural network architecture
    - Reward function design

# Return expectations
expects:
    - Training configuration files
    - Performance benchmarks
    - Behavior documentation
    - Integration instructions
    - Training logs saved
```

### Environment Management (Agent 3)
```python
# Delegation criteria
delegate_when:
    - Python environment issues
    - MCP server setup/debugging
    - Build pipeline configuration
    - Dependency management
    - Deployment preparation

# Return expectations
expects:
    - Environment verified functional
    - Activation scripts updated
    - Dependencies documented
    - Build logs provided
    - Configuration saved to memory
```

### Documentation (Agent 4)
```python
# Delegation criteria
delegate_when:
    - Code documentation needed
    - Memory organization required
    - Knowledge base updates
    - Solution archiving
    - Pattern extraction

# Return expectations
expects:
    - Comprehensive documentation
    - Memory properly categorized
    - Knowledge base updated
    - Patterns identified and saved
    - Duplicates consolidated
```

## 🚨 Critical Decision Points

### When to Escalate
```python
if issue.severity == "critical":
    if affects("Game Creator core"):
        escalate_immediately()
    elif affects("ML training pipeline"):
        document_and_escalate()
    elif affects("production build"):
        stop_all_work_and_escalate()

if issue.frequency > 3:
    create_permanent_solution()
    update_knowledge_base()
    notify_team()
```

### When to Create New Memory
```python
save_memory_when:
    - New error encountered and solved
    - Pattern discovered
    - Performance improvement found
    - Configuration that works
    - Workflow optimization identified
    - Integration solution developed
```

### When to Consolidate
```python
consolidate_when:
    - Similar errors (similarity > 0.85)
    - Duplicate patterns found
    - Fragment becomes solution
    - Multiple partial solutions exist
    - Weekly maintenance window
```

## 📊 Quality Gates

### Before Code Submission
```yaml
unity_checks:
  - compilation: must_pass
  - play_mode_test: must_pass
  - console_errors: zero_tolerance
  - console_warnings: document_all
  - performance: within_budget

gamecreator_checks:
  - module_compatibility: verified
  - custom_actions: documented
  - save_system: tested
  - multiplayer_sync: verified

memory_checks:
  - solution_saved: required
  - patterns_documented: required
  - fragments_updated: required
  - consolidation_run: if_needed
```

### Before Training ML-Agents
```yaml
pre_training:
  - config_validated: required
  - observation_space: verified
  - action_space: correct
  - reward_function: tested
  - curriculum: if_applicable

post_training:
  - metrics_saved: required
  - model_tested: required
  - behavior_documented: required
  - integration_verified: required
```

## 🔁 Feedback Loops

### Continuous Improvement
```python
every_task_completion:
    1. evaluate_solution_effectiveness()
    2. update_memory_with_lessons()
    3. identify_patterns()
    4. optimize_workflow()
    5. share_knowledge()

weekly_review:
    1. analyze_memory_usage()
    2. identify_common_problems()
    3. create_preventive_solutions()
    4. update_documentation()
    5. optimize_recall_settings()
```

### Performance Monitoring
```python
track_metrics:
    - memory_recall_accuracy
    - solution_reuse_rate
    - task_completion_time
    - error_recurrence_rate
    - documentation_coverage

optimize_when:
    - recall_accuracy < 80%
    - reuse_rate < 60%
    - completion_time increasing
    - errors recurring
    - documentation gaps found
```

## 🛡️ Safety Protocols

### Never Override
```python
protected_systems = [
    "Unity Library folder",
    "Game Creator core modules",
    "ML-Agents package files",
    ".meta files (unless necessary)",
    "Build settings (without backup)"
]

protected_processes = [
    "Training in progress",
    "Build pipeline running",
    "MCP server critical operations",
    "Memory consolidation active"
]
```

### Always Backup
```python
before_major_changes:
    1. backup_current_state()
    2. save_configuration_to_memory()
    3. document_rollback_procedure()
    4. test_in_isolation_first()
    5. verify_recovery_possible()
```

## 🎮 Game-Specific Workflows

### Game Creator Module Integration
```python
workflow_new_module:
    1. check_compatibility(module, existing_modules)
    2. search_memory(f"Game Creator {module} integration")
    3. create_test_scene()
    4. implement_basic_setup()
    5. test_all_interactions()
    6. document_patterns()
    7. save_to_solutions()
```

### ML-Agent Behavior Development
```python
workflow_ml_behavior:
    1. define_observation_space()
    2. design_action_space()
    3. create_reward_function()
    4. configure_training_params()
    5. run_training_iterations()
    6. evaluate_behavior()
    7. integrate_into_game()
    8. save_configuration_to_memory()
```

## 📈 Success Metrics

### Task Completion
- Unity builds: 95% success rate
- Memory recalls: 80% relevance
- Solution reuse: 60% minimum
- Documentation: 100% for public APIs
- Performance: Within Unity Profiler budgets

### System Health
- Memory database: <1GB size
- Recall speed: <500ms
- Consolidation: Weekly completion
- Knowledge base: Monthly updates
- MCP servers: 99% uptime

## 🔮 Continuous Evolution

### Adapt Workflow When
- New Game Creator modules added
- Unity version upgraded
- ML-Agents version changed
- Team processes evolve
- Performance requirements change

### Update Agents When
- New expertise needed
- Workflow bottlenecks identified
- Specialization opportunities found
- Efficiency improvements possible

Remember: This workflow is living documentation. Update it as you learn, optimize as you grow, and share improvements with the team.