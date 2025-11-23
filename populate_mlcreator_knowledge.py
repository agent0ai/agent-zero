#!/usr/bin/env python3
"""
Populate Agent Zero Knowledge Base for MLcreator Project
This script creates and populates the knowledge structure for the MLcreator Unity project.
"""

import os
import json
from datetime import datetime
from pathlib import Path


class MLCreatorKnowledgePopulator:
    def __init__(self, agent_zero_path=".", project_path="D:\\GithubRepos\\MLcreator"):
        self.agent_zero_path = Path(agent_zero_path)
        self.project_path = Path(project_path)
        self.knowledge_base = self.agent_zero_path / "knowledge" / "mlcreator"

    def create_directory_structure(self):
        """Create the knowledge base directory structure"""
        directories = [
            self.knowledge_base / "main",
            self.knowledge_base / "fragments",
            self.knowledge_base / "solutions",
            self.knowledge_base / "instruments"
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"[OK] Created directory: {directory}")

    def create_project_overview(self):
        """Create project overview document"""
        content = """# MLcreator Project Overview

## Project Information
- **Name**: MLcreator
- **Type**: Unity 3D Game Development Framework
- **Unity Version**: 2022.3.16f1
- **Primary Language**: C#
- **Secondary Language**: Python (for tools and ML)
- **Location**: D:\\GithubRepos\\MLcreator

## Project Purpose
MLcreator is an advanced Unity game development framework that combines:
1. Game Creator 2 modular system for rapid game development
2. Unity ML-Agents for AI-driven gameplay
3. Multiple MCP servers for enhanced development capabilities
4. Custom tools and automation scripts

## Technology Stack

### Unity Components
- Unity 2022.3.16f1 LTS
- Universal Render Pipeline (URP)
- Input System Package
- Addressables for asset management
- TextMeshPro for UI

### Game Creator Modules
- **Core**: Base framework and character controller
- **Behavior**: AI and state machines
- **Dialogue**: Conversation system
- **Inventory**: Item management
- **Quests**: Mission system
- **Stats**: RPG statistics
- **Perception**: Sensory systems
- **Shooter**: Combat mechanics
- **Multiplayer**: Network synchronization

### ML & AI
- Unity ML-Agents Toolkit
- Python 3.10.11 for training
- TensorFlow/PyTorch backends
- Custom reward functions
- Behavior cloning capabilities

### Development Tools
- Multiple MCP servers (Serena, etc.)
- Python automation scripts
- PowerShell activation scripts
- Custom Unity editor tools
- CI/CD pipeline integration

## Architecture Overview

### Project Structure
```
MLcreator/
├── Assets/               # Unity assets and code
│   ├── Plugins/         # Game Creator and third-party
│   ├── Scripts/         # Custom game scripts
│   └── ML-Agents/       # ML training environments
├── ML_AgentsConfig/     # Training configurations
├── Library/            # Unity generated (gitignored)
├── Packages/           # Package manifest
├── ProjectSettings/    # Unity project settings
├── scripts/            # Automation tools
├── claudedocs/         # AI-generated docs
└── serena-env/         # Python environment
```

### Key Integrations
1. **Game Creator + ML-Agents**: AI-driven NPCs using Game Creator actions
2. **MCP Servers**: Enhanced IDE capabilities and code analysis
3. **Python Tools**: Automation, analysis, and training pipelines
4. **Version Control**: Git with LFS for large assets

## Development Workflow
1. Environment activation based on task type
2. Unity Editor for scene and gameplay development
3. Visual Studio/VS Code for C# scripting
4. Python scripts for automation and ML training
5. MCP servers for enhanced development features

## Performance Targets
- **FPS**: 60+ on target hardware
- **Build Size**: <2GB for desktop
- **Load Time**: <10 seconds initial
- **Memory**: <4GB RAM usage
- **ML Inference**: <10ms per decision

## Current State
- Core framework established
- Game Creator modules integrated
- ML-Agents pipeline functional
- Basic gameplay systems implemented
- Multiplayer foundation in place

## Next Milestones
1. Complete AI behavior system
2. Optimize performance bottlenecks
3. Enhance multiplayer stability
4. Implement advanced ML behaviors
5. Polish UI/UX systems
"""

        filepath = self.knowledge_base / "main" / "project_overview.md"
        filepath.write_text(content, encoding='utf-8')
        print(f"✅ Created: {filepath}")

    def create_architecture_doc(self):
        """Create architecture documentation"""
        content = """# MLcreator Architecture Documentation

## System Architecture

### Core Systems

#### Game Creator Framework
- **Modular Design**: Each system is independent but interconnected
- **Event-Driven**: Uses Game Creator's event system for communication
- **State Management**: Centralized state through Stats module
- **Save System**: Integrated persistence across all modules

#### Unity Architecture
```
Assets/
├── _Project/              # Project-specific assets
│   ├── Scripts/
│   │   ├── Player/      # Player controllers
│   │   ├── AI/          # AI behaviors
│   │   ├── UI/          # User interface
│   │   └── Systems/     # Game systems
│   ├── Prefabs/         # Reusable objects
│   └── Resources/       # Runtime-loaded assets
├── Plugins/              # Third-party code
│   └── GameCreator/     # GC modules
└── StreamingAssets/     # Data files
```

#### Component Architecture
1. **GameObject Hierarchy**
   - Managers (singleton)
   - Player systems
   - Environment
   - UI Canvas
   - Network objects

2. **Script Organization**
   - MonoBehaviours for Unity lifecycle
   - ScriptableObjects for data
   - Pure C# for logic
   - Interfaces for contracts

### Data Flow

#### Game State Flow
```
Input -> Character Controller -> Game Creator Actions -> State Changes -> UI Updates
                                            ↓
                                     ML-Agent Decisions
```

#### ML-Agent Integration
```
Observations -> Neural Network -> Actions -> Game Creator Execution
      ↑                                              ↓
Environment State <----------------------- State Changes
```

### Memory Management

#### Object Pooling
- Projectiles and effects pooled
- Dynamic object limit: 1000
- Automatic cleanup on scene change

#### Asset Management
- Addressables for dynamic loading
- Resource budget: 2GB RAM
- Texture streaming for large worlds

### Network Architecture

#### Multiplayer Setup
- **Host-Client**: Authoritative server model
- **Synchronization**: Game Creator Multiplayer module
- **Tick Rate**: 30Hz for gameplay
- **Interpolation**: Client-side prediction

#### Data Synchronization
1. Transform sync (position, rotation)
2. Animation state sync
3. Game Creator variable sync
4. Custom RPC for events

### Performance Architecture

#### Optimization Strategies
1. **LOD System**: 3 levels of detail
2. **Occlusion Culling**: Frustum + occlusion
3. **Batching**: Static and dynamic
4. **Texture Atlasing**: UI and sprites
5. **Script Optimization**: Object caching

#### Profiling Targets
- **CPU**: <16ms main thread
- **GPU**: <16ms render time
- **Memory**: <100MB/minute growth
- **GC**: <1ms per frame

### Build Pipeline

#### Platform Targets
- **Windows**: Primary platform (DirectX 11)
- **Mac**: Secondary (Metal)
- **Linux**: Experimental (Vulkan)

#### Build Configuration
```json
{
  "compression": "LZ4HC",
  "scripting_backend": "IL2CPP",
  "api_level": ".NET Standard 2.1",
  "optimization": "Master"
}
```

### Security Architecture

#### Data Protection
- Input validation on all user data
- Encrypted save files
- Secure network communication
- Anti-cheat considerations

#### Code Security
- Assembly definitions for isolation
- Code stripping for release
- Obfuscation for critical logic

## Design Patterns

### Singleton Manager
```csharp
public class GameManager : Singleton<GameManager>
{
    // Centralized game state
}
```

### Observer Pattern
```csharp
// Game Creator's event system
Message.Send<PlayerDamaged>(damage);
```

### Factory Pattern
```csharp
// Object creation through factories
var enemy = EnemyFactory.Create(type);
```

### Command Pattern
```csharp
// Game Creator Actions as commands
public class CustomAction : TAction
{
    protected override Status Run() { }
}
```

### State Machine
```csharp
// Game Creator Behavior module
StateMachine.ChangeState(newState);
```

## Integration Points

### Game Creator Integration
- Custom actions in `Runtime/Actions/`
- Custom conditions in `Runtime/Conditions/`
- Custom events in `Runtime/Events/`
- Extension methods in `Extensions/`

### ML-Agents Integration
- Agent scripts in `AI/Agents/`
- Training configs in `ML_AgentsConfig/`
- Decision requesters on AI GameObjects
- Behavior parameters for mode switching

### Tool Integration
- Editor scripts in `Editor/Tools/`
- Build processors in `Editor/Build/`
- Custom inspectors for components
- Project window extensions

## Best Practices

### Code Organization
1. One class per file
2. Namespace everything
3. Regions for organization
4. XML documentation on public API

### Performance Guidelines
1. Cache component references
2. Use object pooling
3. Avoid runtime allocations
4. Profile before optimizing

### Game Creator Guidelines
1. Extend, don't modify core
2. Use the event system
3. Follow naming conventions
4. Document custom modules

## Technical Debt

### Known Issues
1. Memory leak in pooling system (tracked)
2. Multiplayer lag compensation (in progress)
3. ML-Agent training instability (investigating)

### Planned Refactors
1. Input system migration
2. Render pipeline upgrade
3. Save system optimization
4. Network code cleanup

## Dependencies

### Critical Dependencies
- Unity 2022.3.16f1 (exact version)
- Game Creator 2.4.x
- ML-Agents 2.3.x
- .NET Standard 2.1

### Development Dependencies
- Python 3.10.11
- Node.js 18.x (for MCP servers)
- PowerShell 7.x
- Git with LFS
"""

        filepath = self.knowledge_base / "main" / "architecture.md"
        filepath.write_text(content, encoding='utf-8')
        print(f"✅ Created: {filepath}")

    def create_conventions_doc(self):
        """Create coding conventions document"""
        content = """# MLcreator Coding Conventions

## C# Coding Standards

### Naming Conventions

#### Classes and Interfaces
```csharp
public class PlayerController { }      // PascalCase
public interface IInteractable { }     // I prefix for interfaces
public abstract class BaseEnemy { }    // Base prefix for abstract
```

#### Methods and Properties
```csharp
public void PerformAction() { }        // PascalCase for public
private void calculateDamage() { }     // camelCase for private
public int Health { get; set; }        // PascalCase for properties
```

#### Variables and Fields
```csharp
public int maxHealth = 100;            // camelCase for public fields
private int _currentHealth;            // underscore prefix for private
protected float moveSpeed;             // camelCase for protected
const int MAX_PLAYERS = 4;             // UPPER_SNAKE for constants
```

#### Unity-Specific
```csharp
[SerializeField] private int damage;   // Serialized private fields
[RequireComponent(typeof(Rigidbody))] // Component dependencies
[Header("Settings")]                   // Inspector organization
[Tooltip("Damage dealt per hit")]     // Inspector help
```

### Code Organization

#### File Structure
```csharp
using System;
using UnityEngine;
using GameCreator.Runtime.Core;        // Third-party after Unity

namespace MLCreator.Gameplay           // Project namespace
{
    /// <summary>
    /// XML documentation for public classes
    /// </summary>
    public class ExampleClass : MonoBehaviour
    {
        #region Constants
        private const int MAX_VALUE = 100;
        #endregion

        #region Fields
        [Header("Configuration")]
        [SerializeField] private int value;

        private float _timer;
        #endregion

        #region Properties
        public int Value => value;
        #endregion

        #region Unity Lifecycle
        private void Awake() { }
        private void Start() { }
        private void Update() { }
        #endregion

        #region Public Methods
        public void PublicMethod() { }
        #endregion

        #region Private Methods
        private void privateMethod() { }
        #endregion
    }
}
```

### Game Creator Conventions

#### Custom Actions
```csharp
[Serializable]
public class ActionExample : TAction
{
    [SerializeField] private PropertyGetGameObject target;
    [SerializeField] private PropertyGetDecimal value;

    protected override Status Run()
    {
        // Implementation
        return Status.Done;
    }
}
```

#### Custom Conditions
```csharp
[Serializable]
public class ConditionExample : TCondition
{
    [SerializeField] private PropertyGetDecimal value;
    [SerializeField] private CompareType comparison;

    protected override bool Run()
    {
        // Return true/false
        return true;
    }
}
```

## Python Coding Standards

### Style Guide (PEP 8)
```python
# Module imports
import os
import sys
from typing import List, Dict, Optional

# Third-party imports
import numpy as np
import tensorflow as tf

# Local imports
from ml_training import config


class MLTrainer:
    '''Class docstring with description.'''

    def __init__(self, config_path: str):
        '''Initialize trainer with config.'''
        self.config_path = config_path
        self._private_var = None

    def train_model(self, epochs: int = 100) -> Dict:
        '''
        Train the model for specified epochs.

        Args:
            epochs: Number of training epochs

        Returns:
            Dictionary with training metrics
        '''
        pass

    def _private_method(self):
        '''Private helper method.'''
        pass


def snake_case_function(param_one: int, param_two: str) -> bool:
    '''Function names in snake_case.'''
    return True


# Constants in UPPER_SNAKE_CASE
MAX_BATCH_SIZE = 32
DEFAULT_LEARNING_RATE = 0.001
```

## Git Conventions

### Commit Messages
```
Type: Brief description (max 50 chars)

Detailed explanation if needed. Wrap at 72 characters.
Explain what and why, not how.

Fixes #123
```

Types:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `style:` Formatting
- `refactor:` Code restructuring
- `perf:` Performance improvement
- `test:` Test addition/modification
- `chore:` Maintenance tasks

### Branch Naming
```
feature/player-combat-system
fix/multiplayer-sync-issue
refactor/ai-behavior-tree
docs/api-documentation
```

## Documentation Standards

### Code Comments
```csharp
// Single line for simple clarifications

/*
 * Multi-line for complex explanations
 * that need more context
 */

/// <summary>
/// XML docs for public API
/// </summary>
/// <param name="value">Parameter description</param>
/// <returns>Return value description</returns>
```

### README Structure
```markdown
# Component Name

## Overview
Brief description

## Features
- Feature 1
- Feature 2

## Usage
Code examples

## Configuration
Settings and options

## API Reference
Public methods and properties
```

## Unity-Specific Guidelines

### Prefab Naming
- `Player_Character`
- `Enemy_Goblin_Variant`
- `UI_HealthBar`
- `FX_Explosion_Large`
- `Audio_Music_Battle`

### Folder Structure
```
Assets/_Project/
├── Animation/      # .anim, .controller
├── Audio/          # .wav, .mp3
├── Materials/      # .mat
├── Models/         # .fbx, .obj
├── Prefabs/        # .prefab
├── Scripts/        # .cs
├── Shaders/        # .shader, .shadergraph
├── Textures/       # .png, .jpg
└── UI/            # UI assets
```

### Scene Naming
- `MainMenu`
- `Level_01_Forest`
- `Level_02_Castle`
- `TestScene_Combat`

## Performance Guidelines

### Memory Management
```csharp
// Cache references
private Transform _transform;
private void Awake()
{
    _transform = transform;  // Cache once
}

// Use object pooling
var projectile = ObjectPool.Get<Projectile>();
// ... use projectile
ObjectPool.Return(projectile);
```

### Optimization Patterns
```csharp
// Avoid per-frame allocations
private readonly List<Collider> _results = new(10);

// Use squared distances
if (Vector3.SqrMagnitude(delta) < range * range)

// Cache coroutines
private WaitForSeconds _wait = new(1f);
```

## Error Handling

### Exception Handling
```csharp
try
{
    // Risky operation
}
catch (SpecificException e)
{
    Debug.LogError($"Operation failed: {e.Message}");
    // Handle gracefully
}
finally
{
    // Cleanup
}
```

### Validation
```csharp
public void SetHealth(int value)
{
    if (value < 0)
    {
        Debug.LogWarning("Health cannot be negative");
        value = 0;
    }
    health = Mathf.Clamp(value, 0, maxHealth);
}
```

## Testing Conventions

### Test Naming
```csharp
[Test]
public void MethodName_StateUnderTest_ExpectedBehavior()
{
    // Arrange
    var sut = new SystemUnderTest();

    // Act
    var result = sut.Method();

    // Assert
    Assert.AreEqual(expected, result);
}
```

### Test Organization
```
Tests/
├── Runtime/
│   ├── PlayerTests.cs
│   └── CombatTests.cs
└── Editor/
    ├── BuildTests.cs
    └── ToolTests.cs
```

## Review Checklist

Before committing:
- [ ] Code compiles without errors
- [ ] No warnings in Unity console
- [ ] Follows naming conventions
- [ ] Includes necessary documentation
- [ ] Passes existing tests
- [ ] Optimized for performance
- [ ] No sensitive data exposed
- [ ] Git commit message follows format
"""

        filepath = self.knowledge_base / "main" / "conventions.md"
        filepath.write_text(content, encoding='utf-8')
        print(f"✅ Created: {filepath}")

    def create_dependencies_doc(self):
        """Create dependencies documentation"""
        content = """# MLcreator Dependencies Documentation

## Unity Package Dependencies

### Core Packages
```json
{
  "dependencies": {
    "com.unity.collab-proxy": "2.0.5",
    "com.unity.ide.visualstudio": "2.0.18",
    "com.unity.ide.vscode": "1.2.5",
    "com.unity.inputsystem": "1.7.0",
    "com.unity.ml-agents": "2.3.0",
    "com.unity.render-pipelines.universal": "14.0.9",
    "com.unity.test-framework": "1.3.9",
    "com.unity.textmeshpro": "3.0.6",
    "com.unity.timeline": "1.7.6",
    "com.unity.ugui": "1.0.0"
  }
}
```

### Game Creator Modules
- **Game Creator 2**: v2.4.15 (Core framework)
- **Behavior**: v2.2.8 (AI and state machines)
- **Dialogue**: v2.1.5 (Conversation system)
- **Inventory**: v2.3.7 (Item management)
- **Quests**: v2.2.3 (Mission system)
- **Stats**: v2.3.9 (RPG statistics)
- **Perception**: v2.1.2 (Sensory systems)
- **Shooter**: v2.2.6 (Combat mechanics)
- **Multiplayer**: v2.0.4 (Network sync)

### Third-Party Assets
- **Fullscreen NanoSave**: Save system enhancement
- **Undream LLMUnity**: LLM integration
- **Cloud USearch**: Search functionality
- **Assembly Graph**: Code visualization
- **MiTschMR Finder2**: Asset search tool

## Python Dependencies

### requirements.txt
```python
# ML Training
mlagents==0.30.0
torch==2.0.1
tensorflow==2.13.0
numpy==1.24.3
gym==0.26.2

# Development Tools
pyright==1.1.329
black==23.9.1
pytest==7.4.2
pylint==2.17.5

# MCP Servers
fastmcp==0.1.0
anthropic-mcp==0.1.0
langchain==0.0.335

# Utilities
python-dotenv==1.0.0
pyyaml==6.0.1
requests==2.31.0
pandas==2.0.3
matplotlib==3.7.2
```

### Python Version Management
- **Primary**: Python 3.10.11 (ML-Agents compatibility)
- **Secondary**: Python 3.11.x (Tools and scripts)
- **Environment Manager**: pyenv-win

## Development Environment

### IDE Requirements
- **Unity Hub**: 3.5.0+
- **Unity Editor**: 2022.3.16f1 (exact)
- **Visual Studio**: 2022 Community
- **VS Code**: Latest with Unity extensions
- **Git**: 2.40+ with LFS

### VS Code Extensions
```json
{
  "recommendations": [
    "Unity.unity-debug",
    "ms-dotnettools.csharp",
    "ms-python.python",
    "ms-vscode.powershell",
    "github.copilot",
    "eamodio.gitlens"
  ]
}
```

### PowerShell Modules
```powershell
# Required modules
Install-Module -Name PSReadLine
Install-Module -Name Terminal-Icons
Install-Module -Name z
Install-Module -Name PSFzf
```

## MCP Server Dependencies

### Serena MCP
```yaml
dependencies:
  python: ">=3.10"
  packages:
    - fastmcp
    - pydantic
    - uvicorn
    - langchain
environment: serena-env
activation: ./activate-ai.ps1
```

### Unity MCP
```yaml
dependencies:
  node: ">=18.0.0"
  packages:
    - "@anthropic/mcp": "latest"
    - "typescript": "^5.0.0"
    - "ws": "^8.0.0"
configuration: claude-code-mcp-config.json
```

## System Requirements

### Minimum Requirements
- **OS**: Windows 10 64-bit
- **CPU**: Intel i5-8400 / AMD Ryzen 5 2600
- **RAM**: 16GB
- **GPU**: GTX 1060 6GB / RX 580 8GB
- **Storage**: 50GB available
- **DirectX**: Version 11

### Recommended Requirements
- **OS**: Windows 11 64-bit
- **CPU**: Intel i7-10700K / AMD Ryzen 7 3700X
- **RAM**: 32GB
- **GPU**: RTX 3070 / RX 6700 XT
- **Storage**: 100GB SSD
- **DirectX**: Version 12

## Build Dependencies

### Windows Build
```xml
<dependencies>
  <runtime>
    <dependency id="VCRedist140" version="14.34" />
    <dependency id="DirectX" version="11.0" />
    <dependency id="dotnet" version="6.0" />
  </runtime>
</dependencies>
```

### Platform SDKs
- **Windows SDK**: 10.0.19041.0
- **Android SDK**: API Level 30 (optional)
- **iOS SDK**: 14.0 (optional, Mac required)

## CI/CD Dependencies

### GitHub Actions
```yaml
dependencies:
  - unity-builder: v2.4.0
  - unity-test-runner: v2.1.0
  - python-setup: v4.7.0
  - cache-action: v3.3.0
```

### Local Build Tools
- **MSBuild**: 17.0+
- **CMake**: 3.20+ (for native plugins)
- **NSIS**: 3.08 (for installer)

## Network Dependencies

### Required Endpoints
```yaml
production:
  - api.unity.com: License validation
  - packages.unity.com: Package downloads
  - github.com: Version control
  - pypi.org: Python packages

development:
  - localhost:5005: ML-Agents training
  - localhost:3000: MCP servers
  - localhost:8080: Development server
```

## Version Compatibility Matrix

| Component | Version | Unity | Python | Game Creator |
|-----------|---------|-------|--------|--------------|
| MLcreator | 1.0.0 | 2022.3.16f1 | 3.10.11 | 2.4.x |
| ML-Agents | 2.3.0 | 2022.3.x | 3.10.x | Compatible |
| URP | 14.0.9 | 2022.3.x | N/A | Compatible |
| Input System | 1.7.0 | 2022.3.x | N/A | Compatible |

## Dependency Update Policy

### Update Schedule
- **Security**: Immediate
- **Bug Fixes**: Weekly
- **Minor**: Monthly review
- **Major**: Quarterly planning

### Testing Requirements
1. Unit tests must pass
2. Integration tests must pass
3. Unity play mode tests required
4. ML training pipeline verified
5. Build successful on all platforms

## Known Conflicts

### Package Conflicts
- Input System vs Legacy Input (use Input System)
- Built-in RP vs URP (use URP)
- Newtonsoft.Json versions (use Unity's)

### Resolution Strategies
```json
{
  "overrides": {
    "com.unity.nuget.newtonsoft-json": "3.2.1"
  }
}
```

## Dependency Management Commands

### Unity Packages
```bash
# Update all packages
unity-package-manager resolve

# Install specific version
unity-package-manager add com.unity.ml-agents@2.3.0
```

### Python Packages
```bash
# Install all dependencies
pip install -r requirements.txt

# Update specific package
pip install --upgrade mlagents

# Check for updates
pip list --outdated
```

### NPM Packages (MCP)
```bash
# Install dependencies
npm install

# Update all packages
npm update

# Audit for vulnerabilities
npm audit
```

## Troubleshooting Dependencies

### Common Issues

1. **Unity Package Conflicts**
   - Clear Library folder
   - Delete Packages lock file
   - Reimport all packages

2. **Python Version Mismatch**
   - Use pyenv to switch versions
   - Create virtual environment
   - Verify with `python --version`

3. **Missing Dependencies**
   - Check error logs
   - Verify installation paths
   - Reinstall affected packages

4. **Build Failures**
   - Verify all SDKs installed
   - Check environment variables
   - Clear build cache
"""

        filepath = self.knowledge_base / "main" / "dependencies.md"
        filepath.write_text(content, encoding='utf-8')
        print(f"✅ Created: {filepath}")

    def create_solutions_docs(self):
        """Create solution documentation"""

        # Unity patterns
        unity_patterns = """# Unity Development Patterns for MLcreator

## Singleton Pattern
```csharp
public class GameManager : MonoBehaviour
{
    private static GameManager _instance;
    public static GameManager Instance
    {
        get
        {
            if (_instance == null)
            {
                _instance = FindObjectOfType<GameManager>();
                if (_instance == null)
                {
                    GameObject go = new GameObject("GameManager");
                    _instance = go.AddComponent<GameManager>();
                    DontDestroyOnLoad(go);
                }
            }
            return _instance;
        }
    }

    private void Awake()
    {
        if (_instance != null && _instance != this)
        {
            Destroy(gameObject);
            return;
        }
        _instance = this;
        DontDestroyOnLoad(gameObject);
    }
}
```

## Object Pooling
```csharp
public class ObjectPool<T> where T : Component
{
    private readonly Queue<T> _pool = new Queue<T>();
    private readonly T _prefab;
    private readonly Transform _parent;

    public ObjectPool(T prefab, int initialSize, Transform parent = null)
    {
        _prefab = prefab;
        _parent = parent;

        for (int i = 0; i < initialSize; i++)
        {
            var obj = Object.Instantiate(_prefab, _parent);
            obj.gameObject.SetActive(false);
            _pool.Enqueue(obj);
        }
    }

    public T Get()
    {
        T obj = _pool.Count > 0
            ? _pool.Dequeue()
            : Object.Instantiate(_prefab, _parent);

        obj.gameObject.SetActive(true);
        return obj;
    }

    public void Return(T obj)
    {
        obj.gameObject.SetActive(false);
        _pool.Enqueue(obj);
    }
}
```

## Coroutine Caching
```csharp
public class OptimizedBehavior : MonoBehaviour
{
    private readonly Dictionary<float, WaitForSeconds> _waitCache = new();

    protected WaitForSeconds GetWait(float seconds)
    {
        if (!_waitCache.ContainsKey(seconds))
        {
            _waitCache[seconds] = new WaitForSeconds(seconds);
        }
        return _waitCache[seconds];
    }

    private IEnumerator ExampleCoroutine()
    {
        yield return GetWait(1f);  // Cached wait
        // Do something
        yield return GetWait(1f);  // Reuses same object
    }
}
```

## Component Caching
```csharp
public class CachedMonoBehaviour : MonoBehaviour
{
    private Transform _transform;
    private Rigidbody _rigidbody;
    private Collider _collider;

    public new Transform transform
    {
        get
        {
            if (_transform == null)
                _transform = base.transform;
            return _transform;
        }
    }

    public new Rigidbody rigidbody
    {
        get
        {
            if (_rigidbody == null)
                _rigidbody = GetComponent<Rigidbody>();
            return _rigidbody;
        }
    }

    public new Collider collider
    {
        get
        {
            if (_collider == null)
                _collider = GetComponent<Collider>();
            return _collider;
        }
    }
}
```

## Event System
```csharp
public static class EventManager
{
    private static readonly Dictionary<Type, Delegate> _events = new();

    public static void Subscribe<T>(Action<T> listener) where T : struct
    {
        if (_events.TryGetValue(typeof(T), out Delegate d))
        {
            _events[typeof(T)] = Delegate.Combine(d, listener);
        }
        else
        {
            _events[typeof(T)] = listener;
        }
    }

    public static void Unsubscribe<T>(Action<T> listener) where T : struct
    {
        if (_events.TryGetValue(typeof(T), out Delegate d))
        {
            _events[typeof(T)] = Delegate.Remove(d, listener);
        }
    }

    public static void Trigger<T>(T eventData) where T : struct
    {
        if (_events.TryGetValue(typeof(T), out Delegate d))
        {
            (d as Action<T>)?.Invoke(eventData);
        }
    }
}
```

## State Machine
```csharp
public abstract class State<T> where T : MonoBehaviour
{
    protected T context;

    public virtual void Enter(T context)
    {
        this.context = context;
    }

    public abstract void Update();
    public virtual void FixedUpdate() { }
    public virtual void Exit() { }
}

public class StateMachine<T> where T : MonoBehaviour
{
    private State<T> _currentState;
    private T _context;

    public StateMachine(T context)
    {
        _context = context;
    }

    public void ChangeState(State<T> newState)
    {
        _currentState?.Exit();
        _currentState = newState;
        _currentState?.Enter(_context);
    }

    public void Update()
    {
        _currentState?.Update();
    }
}
```

## Optimization Patterns

### Distance Checking
```csharp
// Bad - uses expensive square root
if (Vector3.Distance(a, b) < maxDistance) { }

// Good - compares squared distances
if (Vector3.SqrMagnitude(a - b) < maxDistance * maxDistance) { }
```

### String Building
```csharp
// Bad - creates garbage
string result = "Score: " + score + " Time: " + time;

// Good - uses StringBuilder
private static readonly StringBuilder _sb = new StringBuilder();
string result = _sb.Clear()
    .Append("Score: ").Append(score)
    .Append(" Time: ").Append(time)
    .ToString();
```

### Update Optimization
```csharp
public class OptimizedUpdate : MonoBehaviour
{
    private float _updateInterval = 0.1f;
    private float _nextUpdate;

    private void Update()
    {
        if (Time.time >= _nextUpdate)
        {
            _nextUpdate = Time.time + _updateInterval;
            SlowUpdate();
        }

        // Fast update code here
    }

    private void SlowUpdate()
    {
        // Expensive operations every 0.1 seconds
    }
}
```
"""

        filepath = self.knowledge_base / "solutions" / "unity_patterns.md"
        filepath.write_text(unity_patterns, encoding='utf-8')
        print(f"✅ Created: {filepath}")

        # Game Creator solutions
        gc_solutions = """# Game Creator Solutions

## Custom Action Template
```csharp
using System;
using UnityEngine;
using GameCreator.Runtime.Core;

[Serializable]
public class ActionCustomExample : TAction
{
    [SerializeField] private PropertyGetGameObject m_Target;
    [SerializeField] private PropertyGetDecimal m_Value;

    public override string Title => "Custom Example";

    protected override Status Run()
    {
        GameObject target = m_Target.Get(gameObject);
        if (target == null) return Status.Error;

        float value = (float)m_Value.Get(gameObject);

        // Your custom logic here
        Debug.Log($"Executing on {target.name} with value {value}");

        return Status.Done;
    }
}
```

## Custom Condition Template
```csharp
using System;
using UnityEngine;
using GameCreator.Runtime.Core;

[Serializable]
public class ConditionCustomExample : TCondition
{
    [SerializeField] private PropertyGetGameObject m_Target;
    [SerializeField] private CompareType m_Comparison = CompareType.Equal;
    [SerializeField] private PropertyGetDecimal m_Value;

    public override string Title => "Check Custom Value";

    protected override bool Run()
    {
        GameObject target = m_Target.Get(gameObject);
        if (target == null) return false;

        float currentValue = GetCurrentValue(target);
        float compareValue = (float)m_Value.Get(gameObject);

        return Compare.Numeric(currentValue, compareValue, m_Comparison);
    }

    private float GetCurrentValue(GameObject target)
    {
        // Your custom logic to get value
        return 0f;
    }
}
```

## Game Creator + ML-Agents Integration
```csharp
using Unity.MLAgents;
using Unity.MLAgents.Actuators;
using Unity.MLAgents.Sensors;
using GameCreator.Runtime.Core;
using GameCreator.Runtime.Characters;

public class GameCreatorMLAgent : Agent
{
    private Character m_Character;
    private CharacterController m_Controller;

    public override void Initialize()
    {
        m_Character = GetComponent<Character>();
        m_Controller = m_Character.Motion.Controller;
    }

    public override void OnEpisodeBegin()
    {
        // Reset character state
        m_Character.transform.position = GetRandomSpawnPoint();
        m_Character.transform.rotation = Quaternion.identity;
    }

    public override void CollectObservations(VectorSensor sensor)
    {
        // Character state observations
        sensor.AddObservation(m_Character.transform.position);
        sensor.AddObservation(m_Character.Motion.LinearSpeed);
        sensor.AddObservation(m_Character.Driver.IsGrounded);

        // Add Game Creator specific observations
        var stats = m_Character.GetComponent<Stats>();
        if (stats != null)
        {
            sensor.AddObservation(stats.Get("health"));
            sensor.AddObservation(stats.Get("stamina"));
        }
    }

    public override void OnActionReceived(ActionBuffers actions)
    {
        // Apply actions through Game Creator
        float moveX = actions.ContinuousActions[0];
        float moveZ = actions.ContinuousActions[1];
        bool jump = actions.DiscreteActions[0] > 0;

        // Move character using Game Creator's system
        Vector3 movement = new Vector3(moveX, 0, moveZ);
        m_Character.Motion.MoveToDirection(movement, Space.World);

        if (jump && m_Character.Driver.IsGrounded)
        {
            m_Character.Motion.Jump();
        }
    }
}
```

## Multiplayer Synchronization
```csharp
using UnityEngine;
using Unity.Netcode;
using GameCreator.Runtime.Core;
using GameCreator.Runtime.Characters;

public class NetworkCharacterSync : NetworkBehaviour
{
    private Character m_Character;
    private NetworkVariable<Vector3> m_NetworkPosition = new();
    private NetworkVariable<Quaternion> m_NetworkRotation = new();

    private void Awake()
    {
        m_Character = GetComponent<Character>();
    }

    public override void OnNetworkSpawn()
    {
        if (IsOwner)
        {
            // Send local player data
            InvokeRepeating(nameof(SendCharacterState), 0f, 0.1f);
        }
        else
        {
            // Receive remote player data
            m_NetworkPosition.OnValueChanged += OnPositionChanged;
            m_NetworkRotation.OnValueChanged += OnRotationChanged;
        }
    }

    private void SendCharacterState()
    {
        if (!IsOwner) return;

        UpdatePositionServerRpc(
            m_Character.transform.position,
            m_Character.transform.rotation
        );
    }

    [ServerRpc]
    private void UpdatePositionServerRpc(Vector3 position, Quaternion rotation)
    {
        m_NetworkPosition.Value = position;
        m_NetworkRotation.Value = rotation;
    }

    private void OnPositionChanged(Vector3 previous, Vector3 current)
    {
        if (IsOwner) return;
        m_Character.Teleport.To(current);
    }

    private void OnRotationChanged(Quaternion previous, Quaternion current)
    {
        if (IsOwner) return;
        m_Character.transform.rotation = current;
    }
}
```

## Save System Integration
```csharp
using System;
using UnityEngine;
using GameCreator.Runtime.Core;

[Serializable]
public class CustomSaveData : TSaveData
{
    public float customValue;
    public string customString;
    public int[] customArray;

    public override Type SaveType => typeof(CustomSaveComponent);
}

public class CustomSaveComponent : TSave<CustomSaveData>
{
    private float m_Value;
    private string m_String;
    private int[] m_Array;

    protected override CustomSaveData OnSave()
    {
        return new CustomSaveData
        {
            customValue = m_Value,
            customString = m_String,
            customArray = m_Array
        };
    }

    protected override void OnLoad(CustomSaveData saveData)
    {
        m_Value = saveData.customValue;
        m_String = saveData.customString;
        m_Array = saveData.customArray;
    }
}
```

## Common Issues and Fixes

### Issue: Actions not executing
```csharp
// Problem: Action returns too quickly
protected override Status Run()
{
    StartCoroutine(DoSomething());
    return Status.Done;  // Wrong - coroutine hasn't finished
}

// Solution: Use proper async handling
protected override Status Run()
{
    return Status.Running;  // Return Running for async
}

protected override async Task<Status> RunAsync()
{
    await DoSomethingAsync();
    return Status.Done;
}
```

### Issue: Character not responding
```csharp
// Problem: Direct transform manipulation
transform.position = newPosition;  // Bypasses Game Creator

// Solution: Use Game Creator's systems
m_Character.Teleport.To(newPosition);  // Proper teleport
m_Character.Motion.MoveToPosition(newPosition);  // Smooth movement
```

### Issue: Stats not saving
```csharp
// Ensure Stats component has Save component attached
[RequireComponent(typeof(StatsSave))]
public class CustomStatsComponent : MonoBehaviour
{
    // Component will ensure saves work
}
```
"""

        filepath = self.knowledge_base / "solutions" / "gamecreator_solutions.md"
        filepath.write_text(gc_solutions, encoding='utf-8')
        print(f"✅ Created: {filepath}")

    def create_instruments_docs(self):
        """Create instruments documentation"""

        activation_scripts = """# Activation Scripts Documentation

## Overview
MLcreator uses PowerShell activation scripts to manage different development environments. Each script configures specific tools and environments for different tasks.

## Available Scripts

### activate-ai.ps1
**Purpose**: AI and ML development environment
**Activates**:
- Python 3.10.11 (ML-Agents compatible)
- Serena MCP server environment
- TensorFlow/PyTorch environments
- Jupyter notebook server

**Usage**:
```powershell
./activate-ai.ps1
```

**Environment Variables Set**:
```powershell
$env:PYTHON_VERSION = "3.10.11"
$env:ML_AGENTS_PATH = "./ML_AgentsConfig"
$env:SERENA_ENV = "./serena-env"
$env:MCP_ACTIVE = "serena"
```

### activate-unity.ps1
**Purpose**: Unity development environment
**Activates**:
- Unity 2022.3.16f1 paths
- Visual Studio integration
- Unity-specific tools
- Build environments

**Usage**:
```powershell
./activate-unity.ps1
```

**Environment Variables Set**:
```powershell
$env:UNITY_VERSION = "2022.3.16f1"
$env:UNITY_PATH = "C:/Program Files/Unity/Hub/Editor/2022.3.16f1"
$env:PROJECT_PATH = Get-Location
$env:BUILD_TARGET = "StandaloneWindows64"
```

### activate-devops.ps1
**Purpose**: CI/CD and deployment environment
**Activates**:
- Build tools
- Docker environment
- GitHub CLI
- Deployment scripts

**Usage**:
```powershell
./activate-devops.ps1
```

**Features**:
- Automated build pipeline
- Test execution environment
- Deployment preparation
- Version management

### activate-web.ps1
**Purpose**: Web services and API development
**Activates**:
- Node.js environment
- Web server configurations
- API development tools
- MCP web servers

**Usage**:
```powershell
./activate-web.ps1
```

### activate-environment.ps1
**Purpose**: General environment manager
**Features**:
- Auto-detects required environment
- Manages multiple Python versions
- Handles environment conflicts
- Provides environment status

**Usage**:
```powershell
# Auto-detect and activate
./activate-environment.ps1

# Specific environment
./activate-environment.ps1 -Environment "ai"
```

## Script Functions

### Common Functions
```powershell
function Test-Environment {
    param([string]$EnvName)
    # Validates environment is properly configured
}

function Set-PythonVersion {
    param([string]$Version)
    # Switches Python version using pyenv
}

function Start-MCPServer {
    param([string]$ServerName)
    # Starts specified MCP server
}

function Verify-Dependencies {
    # Checks all required dependencies
}
```

## Environment Variables

### Global Variables
```powershell
$env:MLCREATOR_ROOT = "D:/GithubRepos/MLcreator"
$env:AGENT_ZERO_ROOT = "D:/GithubRepos/agent-zero"
$env:PROJECT_NAME = "MLcreator"
$env:DEVELOPMENT_MODE = "true"
```

### Python Environments
```powershell
# ML-Agents environment
$env:MLAGENTS_ENV = "./ml-agents-env"
$env:MLAGENTS_PYTHON = "3.10.11"

# Serena environment
$env:SERENA_ENV = "./serena-env"
$env:SERENA_PYTHON = "3.10.11"

# Tools environment
$env:TOOLS_ENV = "./tools-env"
$env:TOOLS_PYTHON = "3.11.5"
```

## Troubleshooting

### Common Issues

#### Python Version Conflicts
```powershell
# Check current Python
python --version

# Force specific version
./activate-environment.ps1 -ForceVersion "3.10.11"
```

#### MCP Server Not Starting
```powershell
# Check server status
Get-Process | Where-Object {$_.Name -like "*mcp*"}

# Restart server
./activate-ai.ps1 -RestartServers
```

#### Unity Path Not Found
```powershell
# Manually set Unity path
$env:UNITY_PATH = "Your/Unity/Path"
./activate-unity.ps1
```

## Integration with Agent Zero

### Auto-Activation
Agent Zero can automatically activate appropriate environments:
```python
# In Agent Zero memory
if task.requires("Unity"):
    run_command("./activate-unity.ps1")
elif task.requires("ML-Training"):
    run_command("./activate-ai.ps1")
```

### Environment Detection
```python
def detect_required_environment(task):
    if "Unity" in task or "Game Creator" in task:
        return "unity"
    elif "ML" in task or "training" in task:
        return "ai"
    elif "deploy" in task or "build" in task:
        return "devops"
    return "general"
```

## Best Practices

1. **Always activate before work**:
   - Ensures correct tool versions
   - Sets proper paths
   - Configures environment variables

2. **Use appropriate script for task**:
   - Unity work → activate-unity.ps1
   - ML training → activate-ai.ps1
   - Building → activate-devops.ps1

3. **Check environment status**:
   ```powershell
   ./activate-environment.ps1 -Status
   ```

4. **Clean environment on issues**:
   ```powershell
   ./activate-environment.ps1 -Clean
   ```

## Script Customization

### Adding New Environments
```powershell
# In activate-environment.ps1
$Environments["custom"] = @{
    PythonVersion = "3.11.0"
    RequiredPackages = @("package1", "package2")
    EnvironmentVars = @{
        CUSTOM_VAR = "value"
    }
}
```

### Extending Existing Scripts
```powershell
# Add to existing script
function Custom-Setup {
    # Your custom setup
}

# Call in main flow
Custom-Setup
```
"""

        filepath = self.knowledge_base / "instruments" / "activation_scripts.md"
        filepath.write_text(activation_scripts, encoding='utf-8')
        print(f"✅ Created: {filepath}")

    def run(self):
        """Execute the population process"""
        print("[START] Starting MLcreator Knowledge Base Population")
        print("=" * 50)

        # Create structure
        self.create_directory_structure()

        # Create documents
        print("\n📝 Creating knowledge documents...")
        self.create_project_overview()
        self.create_architecture_doc()
        self.create_conventions_doc()
        self.create_dependencies_doc()
        self.create_solutions_docs()
        self.create_instruments_docs()

        print("\n✅ Knowledge base population complete!")
        print(f"📁 Location: {self.knowledge_base}")

        # Create summary
        summary = {
            "timestamp": datetime.now().isoformat(),
            "knowledge_base": str(self.knowledge_base),
            "documents_created": [
                "main/project_overview.md",
                "main/architecture.md",
                "main/conventions.md",
                "main/dependencies.md",
                "solutions/unity_patterns.md",
                "solutions/gamecreator_solutions.md",
                "instruments/activation_scripts.md"
            ],
            "status": "success"
        }

        summary_path = self.knowledge_base / "population_summary.json"
        summary_path.write_text(json.dumps(summary, indent=2), encoding='utf-8')
        print(f"\n📊 Summary saved to: {summary_path}")


if __name__ == "__main__":
    # Run the population script
    populator = MLCreatorKnowledgePopulator()
    populator.run()