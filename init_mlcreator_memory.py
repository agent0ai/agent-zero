#!/usr/bin/env python3
"""
Initialize Agent Zero Memory for MLcreator Project
This script populates initial memories for the MLcreator Unity project.
"""

import asyncio
import sys
import os
from datetime import datetime
from pathlib import Path

# Add Agent Zero to path
sys.path.insert(0, str(Path(__file__).parent))

from python.helpers.memory import Memory
from agent import Agent, AgentConfig
import models
import initialize


class MLCreatorMemoryInitializer:
    def __init__(self):
        self.memory_subdir = "mlcreator"
        self.memories_to_create = []

    def prepare_memories(self):
        """Prepare all memories to be inserted"""

        # Project context
        self.memories_to_create.append({
            "text": """MLcreator Project Context:
            - Unity 2022.3.16f1 project with Game Creator 2
            - Located at D:\\GithubRepos\\MLcreator
            - Uses ML-Agents for AI training
            - Multiple MCP servers for development
            - Python 3.10.11 for ML training
            - Custom activation scripts for environment management""",
            "metadata": {
                "area": "main",
                "category": "project",
                "tags": ["mlcreator", "context", "overview"],
                "importance": "critical"
            }
        })

        # Common Unity errors and solutions
        self.memories_to_create.append({
            "text": """Unity Error: NullReferenceException
            Context: Trying to access component that hasn't been initialized
            Solution:
            1. Always null-check: if (component != null)
            2. Use [RequireComponent] attribute
            3. Initialize in Awake() not Start()
            4. Cache component references
            Example:
            private Rigidbody _rb;
            void Awake() { _rb = GetComponent<Rigidbody>(); }""",
            "metadata": {
                "area": "solutions",
                "category": "unity_error",
                "tags": ["unity", "error", "nullreference"],
                "importance": "high"
            }
        })

        # Game Creator patterns
        self.memories_to_create.append({
            "text": """Game Creator Action Pattern:
            Module: Core
            Implementation:
            [Serializable]
            public class ActionTemplate : TAction
            {
                [SerializeField] private PropertyGetGameObject m_Target;
                protected override Status Run()
                {
                    GameObject target = m_Target.Get(gameObject);
                    // Implementation
                    return Status.Done;
                }
            }""",
            "metadata": {
                "area": "solutions",
                "category": "pattern",
                "tags": ["gamecreator", "action", "pattern"],
                "importance": "high"
            }
        })

        # ML-Agents configuration
        self.memories_to_create.append({
            "text": """ML-Agents Training Configuration:
            Python: 3.10.11 (required version)
            Activation: ./activate-ai.ps1
            Config location: ML_AgentsConfig/
            Training command: mlagents-learn config.yaml --run-id=test
            Common hyperparameters:
            - batch_size: 128
            - buffer_size: 10240
            - learning_rate: 3e-4
            - num_epochs: 3""",
            "metadata": {
                "area": "main",
                "category": "configuration",
                "tags": ["ml-agents", "training", "config"],
                "importance": "high"
            }
        })

        # Performance optimization
        self.memories_to_create.append({
            "text": """Unity Performance Optimization:
            1. Use object pooling for frequently spawned objects
            2. Cache component references in Awake()
            3. Use squared magnitude for distance checks
            4. Avoid per-frame allocations
            5. Use LOD systems for complex models
            6. Batch draw calls with SRP Batcher
            7. Profile with Unity Profiler regularly
            Target: 60 FPS on GTX 1060""",
            "metadata": {
                "area": "solutions",
                "category": "optimization",
                "tags": ["unity", "performance", "optimization"],
                "importance": "high"
            }
        })

        # Environment setup
        self.memories_to_create.append({
            "text": """Environment Activation Guide:
            Unity Development: ./activate-unity.ps1
            ML Training: ./activate-ai.ps1
            Build Pipeline: ./activate-devops.ps1
            Web Services: ./activate-web.ps1
            Auto-detect: ./activate-environment.ps1
            Python versions: 3.10.11 (ML), 3.11.5 (tools)
            Always activate appropriate environment before work""",
            "metadata": {
                "area": "main",
                "category": "environment",
                "tags": ["environment", "setup", "activation"],
                "importance": "critical"
            }
        })

        # Common workflows
        self.memories_to_create.append({
            "text": """Unity to Game Creator Integration Workflow:
            1. Create new C# script inheriting from TAction/TCondition
            2. Add [Serializable] attribute
            3. Implement Run() or RunAsync() method
            4. Use PropertyGet for inspector fields
            5. Place in Assets/Plugins/GameCreator/Custom/
            6. Refresh Unity to see in Game Creator menus
            7. Test in play mode before building""",
            "metadata": {
                "area": "solutions",
                "category": "workflow",
                "tags": ["gamecreator", "integration", "workflow"],
                "importance": "high"
            }
        })

        # MCP server configuration
        self.memories_to_create.append({
            "text": """MCP Server Configuration:
            Serena MCP: Python-based, semantic code analysis
            Location: ./serena-env
            Activation: Part of ./activate-ai.ps1
            Config: claude-code-mcp-config.json
            Features: Code search, symbol analysis, project management
            Troubleshooting: Check python version, restart if timeout""",
            "metadata": {
                "area": "main",
                "category": "mcp",
                "tags": ["mcp", "serena", "configuration"],
                "importance": "medium"
            }
        })

        # Build settings
        self.memories_to_create.append({
            "text": """Unity Build Configuration:
            Platform: StandaloneWindows64
            Scripting Backend: IL2CPP
            API Level: .NET Standard 2.1
            Compression: LZ4HC
            Target FPS: 60
            Build location: Builds/Windows/
            Pre-build: Run tests, check console errors
            Post-build: Test on target hardware""",
            "metadata": {
                "area": "main",
                "category": "build",
                "tags": ["unity", "build", "configuration"],
                "importance": "high"
            }
        })

        # Git workflow
        self.memories_to_create.append({
            "text": """Git Workflow for MLcreator:
            Branch naming: feature/description, fix/issue
            Commit format: type: brief description
            Types: feat, fix, docs, style, refactor, perf, test
            Before commit: No Unity errors, tests pass
            Large files: Use Git LFS for assets
            Never commit: Library/, Temp/, Logs/
            Always commit: .meta files for assets""",
            "metadata": {
                "area": "main",
                "category": "git",
                "tags": ["git", "version_control", "workflow"],
                "importance": "high"
            }
        })

    async def initialize_memory(self):
        """Initialize memory database with prepared memories"""
        print("🧠 Initializing memory database...")

        # Initialize agent configuration
        agent_config = initialize.initialize_agent()

        # Create a minimal agent for memory access
        agent = Agent(
            number=0,
            config=agent_config,
            context=None
        )

        # Get memory instance
        db = await Memory.get_by_subdir(
            memory_subdir=self.memory_subdir,
            log_item=None,
            preload_knowledge=True
        )

        print(f"📝 Inserting {len(self.memories_to_create)} memories...")

        # Insert each memory
        memory_ids = []
        for i, memory_data in enumerate(self.memories_to_create, 1):
            try:
                memory_id = await db.insert_text(
                    text=memory_data["text"],
                    metadata=memory_data["metadata"]
                )
                memory_ids.append(memory_id)
                print(f"  ✅ Memory {i}/{len(self.memories_to_create)}: {memory_data['metadata']['category']}")
            except Exception as e:
                print(f"  ❌ Failed to insert memory {i}: {e}")
            
            # Manual throttle to avoid quota limits
            await asyncio.sleep(5)

        print(f"\n✅ Successfully initialized {len(memory_ids)} memories")
        return memory_ids

    async def verify_memory(self):
        """Verify memories were properly saved"""
        print("\n🔍 Verifying memory initialization...")

        # Get memory instance
        db = await Memory.get_by_subdir(
            memory_subdir=self.memory_subdir,
            log_item=None,
            preload_knowledge=False
        )

        # Test searches
        test_queries = [
            ("Unity error", "solutions"),
            ("Game Creator", "solutions"),
            ("ML-Agents", "main"),
            ("activation script", "main"),
            ("performance", "solutions")
        ]

        for query, expected_area in test_queries:
            results = await db.search_similarity_threshold(
                query=query,
                limit=5,
                threshold=0.6
            )
            if results:
                print(f"  ✅ Found {len(results)} results for '{query}'")
                # Check if expected area is in results
                areas = [doc.metadata.get("area") for doc in results]
                if expected_area in areas:
                    print(f"     → Found in expected area: {expected_area}")
            else:
                print(f"  ⚠️ No results for '{query}'")

    def create_activation_script(self):
        """Create batch script for easy activation"""
        script_content = """@echo off
echo =====================================
echo MLcreator Memory Initialization
echo =====================================
echo.

cd /d D:\\GithubRepos\\agent-zero

echo Activating Python environment...
call python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

echo Running memory initialization...
python init_mlcreator_memory.py

if errorlevel 0 (
    echo.
    echo =====================================
    echo SUCCESS: Memory initialized!
    echo =====================================
) else (
    echo.
    echo =====================================
    echo ERROR: Memory initialization failed
    echo =====================================
)

pause
"""

        script_path = Path("init_mlcreator_memory.bat")
        script_path.write_text(script_content)
        print(f"\n📄 Created batch script: {script_path}")

    async def run(self):
        """Execute the initialization process"""
        print("🚀 MLcreator Memory Initialization")
        print("=" * 50)

        # Prepare memories
        print("\n📋 Preparing memories...")
        self.prepare_memories()
        print(f"  → Prepared {len(self.memories_to_create)} memories")

        # Initialize memory
        await self.initialize_memory()

        # Verify
        await self.verify_memory()

        # Create helper script
        self.create_activation_script()

        print("\n" + "=" * 50)
        print("✅ Memory initialization complete!")
        print(f"📁 Memory location: memory/{self.memory_subdir}/")
        print("\nNext steps:")
        print("1. Run Agent Zero")
        print("2. Set memory_subdir to 'mlcreator' in settings")
        print("3. Enable auto-recall for automatic memory retrieval")


if __name__ == "__main__":
    # Run the initialization
    initializer = MLCreatorMemoryInitializer()
    asyncio.run(initializer.run())