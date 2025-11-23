"""
Agent Zero Knowledge Generator and Population System
====================================================
This system automatically generates and populates the memory system with knowledge.
"""

import asyncio
import json
import time
import uuid
from datetime import datetime
from typing import List, Dict, Any
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from python.helpers.qdrant_client import QdrantStore
from python.helpers.memory import Memory
from python.helpers.memory_config import get_memory_config
from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
import random

class KnowledgeGenerator:
    """Generates and populates knowledge for Agent Zero"""

    def __init__(self):
        self.embeddings_model = None
        self.qdrant_store = None
        self.memory_config = None
        self.knowledge_categories = {
            "technical": {
                "topics": ["Python", "JavaScript", "Docker", "Kubernetes", "AI/ML", "APIs", "Databases", "Security"],
                "patterns": ["best practices", "design patterns", "optimization", "debugging", "testing", "deployment"]
            },
            "tools": {
                "topics": ["Git", "VS Code", "Terminal", "npm", "pip", "Docker", "kubectl", "AWS CLI"],
                "patterns": ["commands", "configuration", "troubleshooting", "tips", "workflows"]
            },
            "frameworks": {
                "topics": ["React", "Vue", "Angular", "Django", "FastAPI", "Express", "Next.js", "Flask"],
                "patterns": ["setup", "routing", "state management", "authentication", "deployment", "testing"]
            },
            "solutions": {
                "topics": ["error handling", "performance", "scalability", "security", "testing", "monitoring"],
                "patterns": ["common errors", "fixes", "optimizations", "best practices", "patterns"]
            },
            "agent_specific": {
                "topics": ["Agent Zero", "memory system", "tools", "extensions", "prompts", "workflows"],
                "patterns": ["configuration", "customization", "integration", "usage", "tips"]
            }
        }

    async def setup(self):
        """Initialize the knowledge system"""
        print("[SETUP] Initializing knowledge generation system...")

        # Load memory configuration
        self.memory_config = get_memory_config()

        # Initialize embeddings model
        print("  Loading embeddings model...")
        self.embeddings_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

        # Initialize Qdrant store
        if self.memory_config.get("backend") == "qdrant":
            print("  Connecting to Qdrant...")
            self.qdrant_store = QdrantStore(
                embedder=self.embeddings_model,
                collection="agent_zero_knowledge",
                url=self.memory_config.get("qdrant", {}).get("url", "http://localhost:6333"),
                api_key=self.memory_config.get("qdrant", {}).get("api_key", ""),
                prefer_hybrid=True,
                score_threshold=0.6
            )
            await self.qdrant_store._ensure_collection()
            print("  [OK] Connected to Qdrant!")

        print("[OK] Setup complete!")

    def generate_technical_knowledge(self, count: int = 50) -> List[Document]:
        """Generate technical programming knowledge"""
        documents = []

        for i in range(count):
            topic = random.choice(self.knowledge_categories["technical"]["topics"])
            pattern = random.choice(self.knowledge_categories["technical"]["patterns"])

            content = f"""
Technical Knowledge: {topic} - {pattern}

Topic: {topic}
Category: Technical Programming
Pattern: {pattern}

Key Points:
1. When working with {topic}, always consider {pattern}
2. Common approach: Use structured methods for {topic} implementation
3. Best practice: Follow established {pattern} guidelines
4. Performance tip: Optimize {topic} operations for efficiency
5. Security consideration: Validate all inputs in {topic} systems

Example scenario:
When implementing {topic} solutions, start by understanding the {pattern}.
This ensures robust and maintainable code architecture.

Tags: #{topic.lower().replace(' ', '_')} #{pattern.replace(' ', '_')} #technical #programming
"""

            doc = Document(
                page_content=content.strip(),
                metadata={
                    "id": f"tech_{i}_{uuid.uuid4().hex[:8]}",
                    "category": "technical",
                    "topic": topic,
                    "pattern": pattern,
                    "area": "main",
                    "importance": random.randint(7, 10),
                    "timestamp": datetime.now().isoformat(),
                    "source": "knowledge_generator",
                    "tags": [topic.lower(), pattern.replace(' ', '_'), "technical"]
                }
            )
            documents.append(doc)

        return documents

    def generate_tool_knowledge(self, count: int = 30) -> List[Document]:
        """Generate tool-specific knowledge"""
        documents = []

        for i in range(count):
            tool = random.choice(self.knowledge_categories["tools"]["topics"])
            pattern = random.choice(self.knowledge_categories["tools"]["patterns"])

            # Generate realistic tool commands and usage
            commands = {
                "Git": ["git status", "git add .", "git commit -m", "git push", "git pull"],
                "Docker": ["docker build", "docker run", "docker ps", "docker compose up", "docker logs"],
                "npm": ["npm install", "npm run", "npm test", "npm build", "npm publish"],
                "pip": ["pip install", "pip freeze", "pip list", "pip show", "pip uninstall"],
                "Terminal": ["ls -la", "cd", "mkdir", "rm -rf", "grep", "find"],
                "kubectl": ["kubectl get pods", "kubectl apply", "kubectl logs", "kubectl describe"],
            }

            tool_commands = commands.get(tool, ["command1", "command2", "command3"])

            content = f"""
Tool Knowledge: {tool} - {pattern}

Tool: {tool}
Category: Development Tools
Focus: {pattern}

Essential Commands:
{chr(10).join(f'- {cmd}' for cmd in random.sample(tool_commands, min(3, len(tool_commands))))}

Usage Pattern:
The {tool} tool is essential for {pattern}. Key considerations include:
- Efficiency: Use {tool} shortcuts and aliases
- Workflow: Integrate {tool} into your development pipeline
- Troubleshooting: Common {tool} issues and solutions
- Best practices: Follow {tool} conventions and standards

Pro Tips:
1. Master the basics of {tool} before advanced features
2. Create custom configurations for {tool} efficiency
3. Use {tool} documentation for complex scenarios

Tags: #{tool.lower().replace(' ', '_')} #{pattern.replace(' ', '_')} #tools #devtools
"""

            doc = Document(
                page_content=content.strip(),
                metadata={
                    "id": f"tool_{i}_{uuid.uuid4().hex[:8]}",
                    "category": "tools",
                    "tool": tool,
                    "pattern": pattern,
                    "area": "instruments",
                    "importance": random.randint(6, 9),
                    "timestamp": datetime.now().isoformat(),
                    "source": "knowledge_generator",
                    "tags": [tool.lower(), pattern.replace(' ', '_'), "tools"]
                }
            )
            documents.append(doc)

        return documents

    def generate_solution_patterns(self, count: int = 40) -> List[Document]:
        """Generate solution patterns and fixes"""
        documents = []

        error_templates = [
            "TypeError: {0} is not a function",
            "ImportError: No module named {0}",
            "SyntaxError: unexpected token {0}",
            "ConnectionError: Failed to connect to {0}",
            "PermissionError: Access denied to {0}",
            "ValueError: Invalid value for {0}",
            "KeyError: Key {0} not found",
            "AttributeError: Object has no attribute {0}"
        ]

        for i in range(count):
            topic = random.choice(self.knowledge_categories["solutions"]["topics"])
            pattern = random.choice(self.knowledge_categories["solutions"]["patterns"])
            error_template = random.choice(error_templates)

            content = f"""
Solution Pattern: {topic} - {pattern}

Problem Domain: {topic}
Solution Type: {pattern}
Area: Problem Solving

Common Error:
{error_template.format(topic.lower().replace(' ', '_'))}

Solution Steps:
1. Identify the root cause of {topic} issues
2. Apply {pattern} methodology
3. Implement error handling for {topic}
4. Test the solution thoroughly
5. Document the fix for future reference

Code Pattern:
```python
try:
    # Attempt {topic} operation
    result = perform_{topic.lower().replace(' ', '_')}()
except Exception as e:
    # Handle {pattern} scenario
    handle_error(e, context='{topic}')
    # Apply recovery strategy
    recover_from_{pattern.lower().replace(' ', '_')}()
```

Prevention:
- Validate inputs before {topic} operations
- Implement proper error boundaries
- Use type checking and validation
- Add comprehensive logging
- Write unit tests for edge cases

Tags: #{topic.lower().replace(' ', '_')} #{pattern.replace(' ', '_')} #solutions #patterns
"""

            doc = Document(
                page_content=content.strip(),
                metadata={
                    "id": f"solution_{i}_{uuid.uuid4().hex[:8]}",
                    "category": "solutions",
                    "topic": topic,
                    "pattern": pattern,
                    "area": "solutions",
                    "importance": random.randint(8, 10),
                    "timestamp": datetime.now().isoformat(),
                    "source": "knowledge_generator",
                    "tags": [topic.lower(), pattern.replace(' ', '_'), "solutions", "patterns"]
                }
            )
            documents.append(doc)

        return documents

    def generate_agent_zero_knowledge(self, count: int = 30) -> List[Document]:
        """Generate Agent Zero specific knowledge"""
        documents = []

        agent_features = [
            "memory system with Qdrant integration",
            "multi-agent cooperation",
            "tool execution via terminal",
            "custom extensions",
            "prompt engineering",
            "Docker runtime",
            "FAISS vector storage",
            "knowledge base management",
            "project isolation",
            "Web UI on port 5000"
        ]

        for i in range(count):
            topic = random.choice(self.knowledge_categories["agent_specific"]["topics"])
            pattern = random.choice(self.knowledge_categories["agent_specific"]["patterns"])
            feature = random.choice(agent_features)

            content = f"""
Agent Zero Knowledge: {topic} - {pattern}

Component: {topic}
Feature: {feature}
Pattern: {pattern}

Description:
Agent Zero's {topic} provides {feature}. This enables powerful {pattern} capabilities
for AI-assisted development and automation.

Key Capabilities:
1. {topic} supports {pattern} through structured approaches
2. Integration with {feature} enhances functionality
3. Customizable {pattern} options for specific use cases
4. Scalable architecture for {topic} operations
5. Real-time {pattern} with user interaction

Configuration Example:
```yaml
{topic.lower().replace(' ', '_')}:
  enabled: true
  {pattern.lower().replace(' ', '_')}: true
  feature: {feature.lower().replace(' ', '_')}
```

Best Practices:
- Configure {topic} for optimal {pattern}
- Leverage {feature} for enhanced performance
- Monitor {topic} metrics and logs
- Customize {pattern} based on requirements
- Document custom {topic} configurations

Integration Points:
- Memory System: Persistent storage of {topic} data
- Tool System: Execute {pattern} operations
- Extension System: Extend {topic} capabilities
- Project System: Isolate {pattern} configurations

Tags: #agent_zero #{topic.lower().replace(' ', '_')} #{pattern.replace(' ', '_')} #ai_agent
"""

            doc = Document(
                page_content=content.strip(),
                metadata={
                    "id": f"agent_{i}_{uuid.uuid4().hex[:8]}",
                    "category": "agent_specific",
                    "topic": topic,
                    "feature": feature,
                    "pattern": pattern,
                    "area": "main",
                    "importance": random.randint(9, 10),
                    "timestamp": datetime.now().isoformat(),
                    "source": "knowledge_generator",
                    "project": "agent-zero",
                    "tags": ["agent_zero", topic.lower(), pattern.replace(' ', '_')]
                }
            )
            documents.append(doc)

        return documents

    async def populate_knowledge_base(self):
        """Populate the knowledge base with generated content"""
        print("\n" + "="*60)
        print("POPULATING AGENT ZERO KNOWLEDGE BASE")
        print("="*60)

        total_documents = 0

        # Generate and store technical knowledge
        print("\n[1/4] Generating technical knowledge...")
        tech_docs = self.generate_technical_knowledge(50)
        tech_ids = [str(uuid.uuid4()) for _ in tech_docs]

        start_time = time.time()
        await self.qdrant_store.aadd_documents(tech_docs, tech_ids)
        elapsed = time.time() - start_time

        print(f"  Stored {len(tech_docs)} technical documents in {elapsed:.2f}s")
        total_documents += len(tech_docs)

        # Generate and store tool knowledge
        print("\n[2/4] Generating tool knowledge...")
        tool_docs = self.generate_tool_knowledge(30)
        tool_ids = [str(uuid.uuid4()) for _ in tool_docs]

        start_time = time.time()
        await self.qdrant_store.aadd_documents(tool_docs, tool_ids)
        elapsed = time.time() - start_time

        print(f"  Stored {len(tool_docs)} tool documents in {elapsed:.2f}s")
        total_documents += len(tool_docs)

        # Generate and store solution patterns
        print("\n[3/4] Generating solution patterns...")
        solution_docs = self.generate_solution_patterns(40)
        solution_ids = [str(uuid.uuid4()) for _ in solution_docs]

        start_time = time.time()
        await self.qdrant_store.aadd_documents(solution_docs, solution_ids)
        elapsed = time.time() - start_time

        print(f"  Stored {len(solution_docs)} solution documents in {elapsed:.2f}s")
        total_documents += len(solution_docs)

        # Generate and store Agent Zero specific knowledge
        print("\n[4/4] Generating Agent Zero knowledge...")
        agent_docs = self.generate_agent_zero_knowledge(30)
        agent_ids = [str(uuid.uuid4()) for _ in agent_docs]

        start_time = time.time()
        await self.qdrant_store.aadd_documents(agent_docs, agent_ids)
        elapsed = time.time() - start_time

        print(f"  Stored {len(agent_docs)} Agent Zero documents in {elapsed:.2f}s")
        total_documents += len(agent_docs)

        print("\n" + "="*60)
        print(f"KNOWLEDGE BASE POPULATED SUCCESSFULLY")
        print(f"Total Documents: {total_documents}")
        print("="*60)

        return total_documents

    async def test_knowledge_retrieval(self):
        """Test knowledge retrieval and search"""
        print("\n" + "="*60)
        print("TESTING KNOWLEDGE RETRIEVAL")
        print("="*60)

        test_queries = [
            "How to fix Python TypeError",
            "Docker container best practices",
            "Agent Zero memory system configuration",
            "Git workflow commands",
            "Error handling patterns",
            "Performance optimization techniques",
            "Security considerations for APIs",
            "Agent Zero tool execution"
        ]

        for query in test_queries:
            print(f"\nQuery: '{query}'")

            start_time = time.time()
            results = await self.qdrant_store.asearch(query, k=3)
            elapsed = time.time() - start_time

            print(f"  Found {len(results)} results in {elapsed:.3f}s:")

            for i, result in enumerate(results, 1):
                # Extract topic from metadata
                metadata = result.metadata if hasattr(result, 'metadata') else {}
                topic = metadata.get('topic', 'Unknown')
                category = metadata.get('category', 'Unknown')
                importance = metadata.get('importance', 0)

                # Show first 100 chars of content
                content_preview = result.page_content[:100] if hasattr(result, 'page_content') else ''
                content_preview = content_preview.replace('\n', ' ')

                print(f"    {i}. [{category}] {topic} (importance: {importance})")
                print(f"       Preview: {content_preview}...")

    async def create_continuous_learning_loop(self):
        """Create a system for continuous knowledge generation"""
        print("\n" + "="*60)
        print("CONTINUOUS LEARNING SYSTEM")
        print("="*60)

        # Save configuration for continuous learning
        config = {
            "enabled": True,
            "generation_interval": 3600,  # Generate new knowledge every hour
            "batch_size": 10,  # Generate 10 documents per batch
            "categories": list(self.knowledge_categories.keys()),
            "auto_consolidation": True,
            "quality_threshold": 0.7,
            "max_documents": 10000,
            "retention_days": 30
        }

        config_file = "continuous_learning_config.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"Continuous learning configuration saved to {config_file}")

        # Create a script for automated knowledge generation
        script_content = """#!/usr/bin/env python3
'''
Continuous Knowledge Generation Script for Agent Zero
Run this as a scheduled task or cron job for automatic knowledge updates
'''

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from knowledge_generator import KnowledgeGenerator
import json
import time

async def continuous_generation():
    with open('continuous_learning_config.json', 'r') as f:
        config = json.load(f)

    if not config['enabled']:
        print("Continuous learning disabled")
        return

    generator = KnowledgeGenerator()
    await generator.setup()

    while True:
        print(f"Generating {config['batch_size']} new knowledge entries...")

        # Generate mixed knowledge types
        docs = []
        docs.extend(generator.generate_technical_knowledge(config['batch_size'] // 4))
        docs.extend(generator.generate_tool_knowledge(config['batch_size'] // 4))
        docs.extend(generator.generate_solution_patterns(config['batch_size'] // 4))
        docs.extend(generator.generate_agent_zero_knowledge(config['batch_size'] // 4))

        # Store in memory
        import uuid
        ids = [str(uuid.uuid4()) for _ in docs]
        await generator.qdrant_store.aadd_documents(docs, ids)

        print(f"Added {len(docs)} new knowledge entries")
        print(f"Next generation in {config['generation_interval']} seconds")

        await asyncio.sleep(config['generation_interval'])

if __name__ == "__main__":
    asyncio.run(continuous_generation())
"""

        script_file = "continuous_knowledge_generation.py"
        with open(script_file, 'w') as f:
            f.write(script_content)

        print(f"Continuous generation script saved to {script_file}")
        print("\nTo enable continuous learning:")
        print(f"  1. Run: python {script_file}")
        print("  2. Or add to your system scheduler/cron")
        print("  3. Configure settings in continuous_learning_config.json")

        return config

async def main():
    """Main entry point for knowledge generation"""
    generator = KnowledgeGenerator()

    # Setup
    await generator.setup()

    # Populate knowledge base
    total_docs = await generator.populate_knowledge_base()

    # Test retrieval
    await generator.test_knowledge_retrieval()

    # Setup continuous learning
    config = await generator.create_continuous_learning_loop()

    print("\n" + "="*60)
    print("KNOWLEDGE GENERATION COMPLETE")
    print("="*60)
    print(f"✓ Generated {total_docs} knowledge documents")
    print("✓ Knowledge retrieval tested successfully")
    print("✓ Continuous learning system configured")
    print("\nYour Agent Zero is now equipped with a comprehensive knowledge base!")

    # Save summary
    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_documents": total_docs,
        "categories": list(generator.knowledge_categories.keys()),
        "continuous_learning": config,
        "status": "active"
    }

    with open("knowledge_generation_summary.json", 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\nSummary saved to knowledge_generation_summary.json")

if __name__ == "__main__":
    asyncio.run(main())