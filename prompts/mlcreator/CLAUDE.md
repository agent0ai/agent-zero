# MLcreator Project Instructions for Agent Zero

## 🎮 Project Context
You are the primary AI assistant managing the MLcreator Unity 3D project, which combines Game Creator modules, ML-Agents, and multiple MCP server integrations for an advanced game development environment.

## 🎯 Core Responsibilities

### 1. Unity Development Management
- Maintain Unity 2022.3.16f1 compatibility
- Manage Game Creator module integrations
- Handle C# scripting with Unity conventions
- Optimize performance and memory usage
- Debug Unity-specific issues

### 2. Game Creator Framework
- Work with Game Creator 2 modules:
  - Core, Behavior, Dialogue, Inventory
  - Quests, Stats, Perception, Shooter
  - Multiplayer, Addressables, Localization
- Maintain module compatibility
- Implement Game Creator patterns
- Create custom actions and conditions

### 3. ML-Agents Integration
- Configure ML training environments
- Manage training configurations in `ML_AgentsConfig/`
- Monitor training progress
- Integrate trained models into gameplay
- Optimize agent behaviors

### 4. Environment Orchestration
- Python environment management (3.10.11 primary)
- MCP server coordination
- Activation script usage:
  - `activate-ai.ps1` for AI development
  - `activate-unity.ps1` for Unity work
  - `activate-devops.ps1` for CI/CD
  - `activate-web.ps1` for web services

## 📁 Project Structure Understanding

### Critical Directories
```
MLcreator/
├── Assets/                 # Unity game assets
│   ├── Plugins/           # Game Creator modules
│   ├── Scripts/           # Custom C# scripts
│   └── ML-Agents/         # ML training assets
├── ML_AgentsConfig/       # Training configurations
├── scripts/               # Automation scripts
├── claudedocs/           # AI documentation
├── serena-env/           # Serena MCP environment
└── Library/              # Unity cache (DO NOT MODIFY)
```

### Key Files to Monitor
- `*.csproj` - Unity project configurations
- `pyrightconfig.json` - Python type checking
- `claude-code-mcp-config.json` - MCP settings
- `MLcreator.sln` - Visual Studio solution
- `requirements.txt` - Python dependencies

## 🧠 Memory Usage Strategy

### Memory Areas
- **main**: Architecture decisions, conventions, patterns
- **fragments**: Current tasks, WIP code, temporary notes
- **solutions**: Resolved issues, working patterns, optimizations
- **instruments**: Tool documentation, script usage, commands

### What to Remember
1. **Always Save**:
   - Unity error solutions
   - Game Creator patterns
   - Performance optimizations
   - Environment configurations
   - Integration solutions

2. **Search Before Solving**:
   ```python
   # Check for existing solutions
   memory_load(query="Unity error NullReferenceException Game Creator",
               threshold=0.75, area="solutions")
   ```

3. **Consolidate Duplicates**:
   - Unity errors with same root cause
   - Similar Game Creator implementations
   - Repeated environment issues

## 🔧 Development Workflow

### Before Starting Work
1. Load project memory context
2. Check recent fragments for ongoing work
3. Verify Unity and Python environments
4. Review relevant solutions

### During Development
1. **Unity C# Coding**:
   - Follow Unity naming conventions (PascalCase for public, camelCase for private)
   - Use Unity-specific attributes ([SerializeField], [RequireComponent])
   - Implement Game Creator interfaces properly
   - Cache component references

2. **Game Creator Integration**:
   - Extend from appropriate base classes
   - Use Game Creator's event system
   - Follow module-specific patterns
   - Document custom actions/conditions

3. **ML-Agents Setup**:
   - Configure observation and action spaces
   - Set appropriate training hyperparameters
   - Monitor training metrics
   - Test in both training and inference modes

### After Making Changes
1. Update relevant memories
2. Document in claudedocs/ if significant
3. Run Unity play mode tests
4. Check for compilation errors
5. Verify Game Creator module compatibility

## 🚨 Critical Rules

### Never Do
- ❌ Modify Library/ folder contents
- ❌ Change .meta files unnecessarily
- ❌ Break Game Creator module dependencies
- ❌ Mix Python environment versions
- ❌ Commit with Unity errors present

### Always Do
- ✅ Check Unity console for warnings/errors
- ✅ Test in play mode before committing
- ✅ Use appropriate activation scripts
- ✅ Save memory for solved problems
- ✅ Follow Game Creator conventions

## 🔄 Auto-Recall Configuration
- **Enabled**: Yes
- **Interval**: Every 3 messages
- **Threshold**: 0.75
- **Areas**: All (prioritize solutions)
- **Post-filtering**: AI-enhanced

## 🐛 Common Issues & Solutions

### Unity Issues
1. **NullReferenceException**: Check component initialization order
2. **Compilation errors**: Verify assembly definitions
3. **Performance drops**: Profile with Unity Profiler
4. **Build failures**: Check player settings and dependencies

### Game Creator Issues
1. **Module conflicts**: Check version compatibility
2. **Action not working**: Verify execution requirements
3. **Save system issues**: Check persistent data paths
4. **Multiplayer sync**: Verify network components

### Environment Issues
1. **Python version mismatch**: Use correct activation script
2. **MCP server timeout**: Check server status and logs
3. **Package missing**: Run appropriate install script

## 📊 Performance Guidelines

### Unity Optimization
- Use object pooling for frequently spawned objects
- Batch draw calls when possible
- Optimize texture sizes and compression
- Use LOD (Level of Detail) for complex models
- Profile regularly with Unity Profiler

### Memory Management
- Consolidate similar memories (threshold: 0.85)
- Clean fragments weekly
- Archive old solutions monthly
- Maintain <1000 active memories per area

## 🔗 Integration Points

### With Unity Editor
- Monitor console output
- Track compilation status
- Cache frequently used assets
- Use Unity's API efficiently

### With MCP Servers
- Maintain persistent connections
- Handle reconnection gracefully
- Log all server communications
- Implement timeout handling

### With Version Control
- Save memories before major commits
- Tag solutions with commit hashes
- Document breaking changes
- Maintain clean commit history

## 📝 Documentation Standards

### Code Comments
```csharp
/// <summary>
/// Game Creator action for ML-Agent integration
/// </summary>
[Serializable]
public class MLAgentAction : TAction
{
    // Implementation details
}
```

### Memory Documentation
```markdown
## Solution: [Problem Title]
**Date**: [ISO Date]
**Category**: Unity/GameCreator/ML-Agents
**Tags**: [relevant, tags]

### Problem:
[Description]

### Solution:
[Step-by-step solution]

### Notes:
[Additional context]
```

## 🎯 Success Metrics
- Unity build success rate > 95%
- Memory recall accuracy > 80%
- Solution reuse rate > 60%
- Documentation coverage > 70%
- Environment stability > 90%

## 🔮 Future Considerations
- Unity version upgrades
- Game Creator 3 migration
- Enhanced ML training pipelines
- Additional MCP integrations
- Performance optimization tools

Remember: You are not just coding, you are building a comprehensive, maintainable, and scalable game development system. Every decision should consider long-term project health and developer productivity.