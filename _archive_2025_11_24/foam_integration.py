#!/usr/bin/env python3
"""
Foam Graph Integration for Agent Zero with Serena Memory System
This script integrates Serena's symbol analysis with Foam's visualization
"""

import os
import json
import re
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Tuple
import hashlib

# Agent Zero imports
import sys
sys.path.insert(0, str(Path(__file__).parent))
from python.helpers.memory import Memory
from agent import Agent


class FoamGraphIntegrator:
    """Integrates Serena's symbol analysis with Foam graph visualization"""

    def __init__(self, project_path: Path = Path(".")):
        self.project_path = project_path
        self.foam_dir = project_path / ".vscode"
        self.foam_json_path = self.foam_dir / "foam.json"
        self.docs_dir = project_path / "docs"
        self.memory_subdir = "agent-zero"
        self.symbol_cache = {}
        self.relationships = []
        self.tags = {}

    def ensure_foam_structure(self):
        """Ensure Foam directory structure exists"""
        self.foam_dir.mkdir(exist_ok=True, parents=True)
        self.docs_dir.mkdir(exist_ok=True)

        # Create default foam.json if not exists
        if not self.foam_json_path.exists():
            default_foam = {
                "purpose": "Agent Zero Knowledge Graph",
                "future": "Automated symbol and memory integration",
                "graph": {
                    "exclude": ["node_modules/**", ".venv/**", "Library/**"],
                    "include": ["**/*.md", "**/*.py", "**/*.ts", "**/*.js"],
                    "linkReferences": "withExtensions"
                },
                "tags": {
                    "enabled": True,
                    "tagDirectory": "tags/",
                    "hierarchicalSeparator": "-"
                }
            }
            self.foam_json_path.write_text(json.dumps(default_foam, indent=2), encoding='utf-8')
            print(f"[OK] Created foam.json at {self.foam_json_path}")

    def extract_symbols_from_file(self, file_path: Path) -> Dict:
        """Extract symbols from a code file"""
        symbols = {
            "classes": [],
            "functions": [],
            "imports": [],
            "exports": [],
            "interfaces": [],
            "references": []
        }

        if not file_path.exists():
            return symbols

        content = file_path.read_text(encoding='utf-8', errors='ignore')

        # Language-specific extraction
        if file_path.suffix == '.py':
            # Python symbols
            symbols["classes"] = re.findall(r'^class\s+(\w+)', content, re.MULTILINE)
            symbols["functions"] = re.findall(r'^def\s+(\w+)', content, re.MULTILINE)
            symbols["imports"] = re.findall(r'^(?:from\s+[\w.]+\s+)?import\s+([\w,\s]+)', content, re.MULTILINE)

        elif file_path.suffix in ['.ts', '.js']:
            # TypeScript/JavaScript symbols
            symbols["classes"] = re.findall(r'(?:export\s+)?class\s+(\w+)', content)
            symbols["functions"] = re.findall(r'(?:export\s+)?(?:async\s+)?function\s+(\w+)', content)
            symbols["interfaces"] = re.findall(r'interface\s+(\w+)', content)
            symbols["imports"] = re.findall(r"import\s+.*?from\s+['\"](.+?)['\"]", content)
            symbols["exports"] = re.findall(r'export\s+(?:default\s+)?(\w+)', content)

        return symbols

    def generate_wikilinks(self, symbols: Dict) -> List[str]:
        """Generate Foam wikilinks for symbols"""
        links = []

        for symbol_type, symbol_list in symbols.items():
            for symbol in symbol_list:
                if symbol and len(symbol) > 2:  # Skip very short symbols
                    link = f"[[{symbol}]]"
                    links.append(link)

        return links

    def generate_tags(self, file_path: Path, symbols: Dict) -> Set[str]:
        """Generate tags for a file based on its symbols"""
        tags = set()

        # File type tags
        suffix_map = {
            '.py': '#python',
            '.ts': '#typescript',
            '.js': '#javascript',
            '.md': '#documentation'
        }
        tags.add(suffix_map.get(file_path.suffix, '#code'))

        # Symbol-based tags
        if symbols["classes"]:
            tags.add("#has-classes")
            for cls in symbols["classes"][:3]:  # Top 3 classes
                tags.add(f"#class-{cls.lower()}")

        if symbols["functions"]:
            tags.add("#has-functions")

        if symbols["interfaces"]:
            tags.add("#has-interfaces")

        # Directory-based tags
        parts = file_path.parts
        if 'python' in parts:
            tags.add("#python-module")
        if 'helpers' in parts:
            tags.add("#helper")
        if 'tools' in parts:
            tags.add("#tool")
        if 'api' in parts:
            tags.add("#api")

        # Importance tags
        important_files = ['agent.py', 'memory.py', 'initialize.py', 'models.py']
        if file_path.name in important_files:
            tags.add("#core")
            tags.add("#important")

        return tags

    def create_symbol_markdown(self, file_path: Path, symbols: Dict, tags: Set[str], links: List[str]):
        """Create a markdown file with symbol information and wikilinks"""
        rel_path = file_path.relative_to(self.project_path)
        doc_name = str(rel_path).replace(os.sep, '_').replace('.', '_') + '.md'
        doc_path = self.docs_dir / 'symbols' / doc_name

        doc_path.parent.mkdir(exist_ok=True, parents=True)

        content = f"""---
tags: {' '.join(sorted(tags))}
created: {datetime.now().isoformat()}
source: {rel_path}
type: symbol-documentation
---

# {file_path.name}

**Path**: `{rel_path}`

## Symbols

### Classes
{chr(10).join(f"- [[{cls}]]" for cls in symbols.get('classes', [])) or "None"}

### Functions
{chr(10).join(f"- [[{func}]]" for func in symbols.get('functions', [])) or "None"}

### Interfaces
{chr(10).join(f"- [[{iface}]]" for iface in symbols.get('interfaces', [])) or "None"}

## Imports
{chr(10).join(f"- `{imp}`" for imp in symbols.get('imports', [])) or "None"}

## References
{chr(10).join(links[:10]) if links else "None"}

## Memory Integration
- Memory Area: #memory-main
- Auto-tagged: {datetime.now().strftime('%Y-%m-%d')}
- Symbol Count: {sum(len(v) for v in symbols.values())}

## Related Files
<!-- Auto-generated by relationship analyzer -->
"""

        doc_path.write_text(content, encoding='utf-8')
        return doc_path

    def analyze_relationships(self, file_path: Path, symbols: Dict) -> List[Tuple[str, str, str]]:
        """Analyze relationships between files based on symbols"""
        relationships = []

        # Check imports for relationships
        for imp in symbols.get('imports', []):
            # Try to resolve import to local file
            possible_paths = [
                self.project_path / f"{imp}.py",
                self.project_path / f"{imp}.ts",
                self.project_path / f"{imp}.js",
                self.project_path / "python" / f"{imp}.py"
            ]

            for possible_path in possible_paths:
                if possible_path.exists():
                    relationships.append((
                        str(file_path.relative_to(self.project_path)),
                        "imports",
                        str(possible_path.relative_to(self.project_path))
                    ))

        return relationships

    async def integrate_with_memory(self, symbols: Dict, file_path: Path):
        """Integrate discovered symbols with Agent Zero memory system"""
        try:
            # Get memory instance
            db = await Memory.get_by_subdir(
                memory_subdir=self.memory_subdir,
                log_item=None,
                preload_knowledge=False
            )

            # Create memory entry for important symbols
            important_symbols = {
                "file": str(file_path.relative_to(self.project_path)),
                "classes": symbols.get("classes", [])[:5],
                "functions": symbols.get("functions", [])[:10],
                "timestamp": datetime.now().isoformat()
            }

            if important_symbols["classes"] or important_symbols["functions"]:
                memory_text = f"""Code Symbols from {file_path.name}:
Classes: {', '.join(important_symbols['classes'])}
Functions: {', '.join(important_symbols['functions'])}
Path: {important_symbols['file']}
Type: Symbol Index"""

                memory_id = await db.insert_text(
                    text=memory_text,
                    metadata={
                        "area": "main",
                        "category": "symbol_index",
                        "file": important_symbols["file"],
                        "tags": ["foam", "symbols", "auto-indexed"],
                        "timestamp": important_symbols["timestamp"]
                    }
                )
                print(f"  [MEMORY] Saved to memory: {memory_id[:8]}...")

        except Exception as e:
            print(f"  [WARNING] Memory integration error: {e}")

    def update_foam_json(self, all_relationships: List[Tuple[str, str, str]]):
        """Update foam.json with discovered relationships"""
        if not self.foam_json_path.exists():
            self.ensure_foam_structure()

        foam_config = json.loads(self.foam_json_path.read_text())

        # Add discovered relationships
        if "relationships" not in foam_config:
            foam_config["relationships"] = []

        for source, rel_type, target in all_relationships:
            rel_entry = {
                "source": source,
                "type": rel_type,
                "target": target,
                "discovered": datetime.now().isoformat()
            }

            # Avoid duplicates
            if rel_entry not in foam_config["relationships"]:
                foam_config["relationships"].append(rel_entry)

        # Add symbol statistics
        foam_config["statistics"] = {
            "last_updated": datetime.now().isoformat(),
            "total_files_analyzed": len(self.symbol_cache),
            "total_relationships": len(foam_config["relationships"]),
            "total_symbols": sum(
                sum(len(v) for v in symbols.values())
                for symbols in self.symbol_cache.values()
            )
        }

        self.foam_json_path.write_text(json.dumps(foam_config, indent=2), encoding='utf-8')
        print(f"[OK] Updated foam.json with {len(all_relationships)} relationships")

    async def process_file(self, file_path: Path):
        """Process a single file for symbols and relationships"""
        print(f"[FILE] Processing: {file_path.relative_to(self.project_path)}")

        # Extract symbols
        symbols = self.extract_symbols_from_file(file_path)
        self.symbol_cache[str(file_path)] = symbols

        # Generate tags and links
        tags = self.generate_tags(file_path, symbols)
        links = self.generate_wikilinks(symbols)

        # Create documentation
        doc_path = self.create_symbol_markdown(file_path, symbols, tags, links)
        print(f"  [DOC] Created: {doc_path.relative_to(self.project_path)}")

        # Analyze relationships
        relationships = self.analyze_relationships(file_path, symbols)
        self.relationships.extend(relationships)

        # Integrate with memory
        await self.integrate_with_memory(symbols, file_path)

    async def run_full_analysis(self):
        """Run full analysis on the project"""
        print("[START] Starting Foam Graph Integration")
        print("=" * 60)

        self.ensure_foam_structure()

        # Find all code files
        extensions = ['.py', '.ts', '.js']
        code_files = []

        for ext in extensions:
            code_files.extend(self.project_path.glob(f"**/*{ext}"))

        # Filter out ignored paths
        ignored_dirs = ['node_modules', '.venv', 'Library', '__pycache__', '.git']
        code_files = [
            f for f in code_files
            if not any(ignored in str(f) for ignored in ignored_dirs)
        ]

        print(f"Found {len(code_files)} code files to analyze")
        print()

        # Process each file
        for file_path in code_files[:20]:  # Limit for demo
            try:
                await self.process_file(file_path)
            except Exception as e:
                print(f"  [ERROR] Error processing {file_path}: {e}")

        # Update foam.json
        self.update_foam_json(self.relationships)

        # Create index file
        self.create_index_file()

        print()
        print("=" * 60)
        print(f"[OK] Analysis complete!")
        print(f"[STATS] Processed {len(self.symbol_cache)} files")
        print(f"[STATS] Found {len(self.relationships)} relationships")
        print(f"[INFO] Documentation in: {self.docs_dir / 'symbols'}")

    def create_index_file(self):
        """Create an index file for all discovered symbols"""
        index_path = self.docs_dir / "symbol_index.md"

        content = f"""---
tags: #index #symbols #foam #auto-generated
created: {datetime.now().isoformat()}
---

# Symbol Index

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Statistics
- Total Files: {len(self.symbol_cache)}
- Total Relationships: {len(self.relationships)}
- Last Updated: {datetime.now().isoformat()}

## Core Files
"""

        # Group files by directory
        files_by_dir = {}
        for file_path in self.symbol_cache.keys():
            path = Path(file_path)
            dir_name = path.parent.name
            if dir_name not in files_by_dir:
                files_by_dir[dir_name] = []
            files_by_dir[dir_name].append(path.name)

        for dir_name, files in sorted(files_by_dir.items()):
            content += f"\n### {dir_name}/\n"
            for file_name in sorted(files):
                content += f"- [[{file_name}]]\n"

        content += """

## Relationship Graph

See Foam Graph visualization for interactive view.

## Memory Integration Status

[OK] Symbols indexed in Agent Zero memory
[OK] Searchable via memory_load()
[OK] Auto-tagged for retrieval

## Usage

1. Open VS Code with Foam extension
2. Press `Ctrl+Shift+P` → "Foam: Show Graph"
3. Explore relationships visually
4. Click nodes to navigate to files
"""

        index_path.write_text(content, encoding='utf-8')
        print(f"[INDEX] Created index: {index_path.relative_to(self.project_path)}")


class CronScheduler:
    """Scheduler for automated Foam updates"""

    def __init__(self, integrator: FoamGraphIntegrator):
        self.integrator = integrator
        self.running = False

    async def run_scheduled_task(self):
        """Run scheduled analysis task"""
        print(f"\n[SCHEDULE] Running scheduled Foam update at {datetime.now()}")
        await self.integrator.run_full_analysis()

    async def start(self, interval_minutes: int = 30):
        """Start the scheduler"""
        self.running = True
        print(f"[SCHEDULER] Started (interval: {interval_minutes} minutes)")

        while self.running:
            await self.run_scheduled_task()
            await asyncio.sleep(interval_minutes * 60)

    def stop(self):
        """Stop the scheduler"""
        self.running = False
        print("🛑 Scheduler stopped")


async def main():
    """Main entry point"""
    integrator = FoamGraphIntegrator(Path.cwd())

    # Run initial analysis
    await integrator.run_full_analysis()

    # Optional: Start scheduler
    # scheduler = CronScheduler(integrator)
    # await scheduler.start(30)  # Run every 30 minutes


if __name__ == "__main__":
    asyncio.run(main())