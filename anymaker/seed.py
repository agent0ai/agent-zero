#!/usr/bin/env python3
"""
Anymaker Graph Seeder

Seeds the FalkorDB graph with initial Anymaker code, prompts, and schema.
Run once to bootstrap a new graph, or to update code in the graph.
"""

import os
import hashlib
from pathlib import Path
from datetime import datetime


def hash_content(content):
    """Generate SHA256 hash of content."""
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def seed_schema(graph):
    """Create graph schema and indexes."""
    print("Creating schema and indexes...")

    # Indexes for Code nodes
    try:
        graph.query("CREATE INDEX FOR (c:Code) ON (c.name)")
    except:
        pass
    try:
        graph.query("CREATE INDEX FOR (c:Code) ON (c.type)")
    except:
        pass
    try:
        graph.query("CREATE INDEX FOR (c:Code) ON (c.is_current)")
    except:
        pass

    # Indexes for Prompt nodes
    try:
        graph.query("CREATE INDEX FOR (p:Prompt) ON (p.name)")
    except:
        pass
    try:
        graph.query("CREATE INDEX FOR (p:Prompt) ON (p.is_current)")
    except:
        pass

    # Indexes for Agent nodes
    try:
        graph.query("CREATE INDEX FOR (a:Agent) ON (a.id)")
    except:
        pass

    # Platform node
    graph.query("""
        MERGE (p:Platform {id: 'anymaker'})
        ON CREATE SET p.version = '0.1.0', p.created_at = $now
        ON MATCH SET p.version = '0.1.0'
    """, {'now': datetime.now().isoformat()})

    print("Schema created.")


def seed_code(graph, name, code_type, content, scope='platform'):
    """Insert or update a code node in the graph."""
    content_hash = hash_content(content)

    # Check if identical content exists
    existing = graph.query("""
        MATCH (c:Code {name: $name, type: $type, is_current: true})
        RETURN c.content_hash as hash
    """, {'name': name, 'type': code_type})

    if existing.result_set and existing.result_set[0][0] == content_hash:
        print(f"  [skip] {code_type}/{name} (unchanged)")
        return False

    # Mark old version as not current
    graph.query("""
        MATCH (c:Code {name: $name, type: $type, is_current: true})
        SET c.is_current = false
    """, {'name': name, 'type': code_type})

    # Insert new version
    graph.query("""
        CREATE (c:Code {
            name: $name,
            type: $type,
            content: $content,
            content_hash: $hash,
            version: coalesce(
                (MATCH (old:Code {name: $name, type: $type}) RETURN max(old.version)),
                0
            ) + 1,
            is_current: true,
            scope: $scope,
            created_at: $now
        })
    """, {
        'name': name,
        'type': code_type,
        'content': content,
        'hash': content_hash,
        'scope': scope,
        'now': datetime.now().isoformat()
    })

    print(f"  [seed] {code_type}/{name}")
    return True


def seed_prompt(graph, name, content, category='system', scope='platform'):
    """Insert or update a prompt node in the graph."""
    content_hash = hash_content(content)

    # Check if identical content exists
    existing = graph.query("""
        MATCH (p:Prompt {name: $name, is_current: true})
        RETURN p.content_hash as hash
    """, {'name': name})

    if existing.result_set and existing.result_set[0][0] == content_hash:
        print(f"  [skip] prompt/{name} (unchanged)")
        return False

    # Mark old version as not current
    graph.query("""
        MATCH (p:Prompt {name: $name, is_current: true})
        SET p.is_current = false
    """, {'name': name})

    # Insert new version
    graph.query("""
        CREATE (p:Prompt {
            name: $name,
            category: $category,
            content: $content,
            content_hash: $hash,
            version: coalesce(
                (MATCH (old:Prompt {name: $name}) RETURN max(old.version)),
                0
            ) + 1,
            is_current: true,
            scope: $scope,
            created_at: $now
        })
    """, {
        'name': name,
        'category': category,
        'content': content,
        'hash': content_hash,
        'scope': scope,
        'now': datetime.now().isoformat()
    })

    print(f"  [seed] prompt/{name}")
    return True


def seed_runtime(graph):
    """Seed the core runtime code."""
    print("\nSeeding runtime...")

    runtime_code = '''
"""
Anymaker Runtime - Loaded from graph by bootstrap
"""

import sys
from flask import Flask, jsonify

# Install graph module loader
from anymaker import graph_loader
graph_loader.install(graph)

# Create Flask app
app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'platform': 'anymaker',
        'graph': GRAPH_NAME
    })

@app.route('/')
def index():
    return jsonify({
        'message': 'Anymaker is running',
        'endpoints': ['/health', '/api/v1/...']
    })

# Start server
if __name__ == '__main__':
    print(f"\\nAnymaker API starting on port {API_PORT}...")
    app.run(host='0.0.0.0', port=API_PORT)
'''

    seed_code(graph, 'runtime', 'core', runtime_code)


def seed_from_a0(graph, a0_path=None):
    """
    Seed graph from Agent Zero codebase.
    Transforms A0 code for graph-native operation.
    """
    if a0_path is None:
        # Assume we're in the anymaker repo which contains A0 code
        a0_path = Path(__file__).parent.parent

    print(f"\nSeeding from A0 codebase: {a0_path}")

    # Seed tools
    tools_path = a0_path / 'python' / 'tools'
    if tools_path.exists():
        print("\nSeeding tools...")
        for f in tools_path.glob('*.py'):
            if f.name.startswith('_'):
                continue
            name = f.stem
            content = f.read_text()
            seed_code(graph, name, 'tool', content)

    # Seed helpers
    helpers_path = a0_path / 'python' / 'helpers'
    if helpers_path.exists():
        print("\nSeeding helpers...")
        for f in helpers_path.glob('*.py'):
            if f.name.startswith('_'):
                continue
            name = f.stem
            content = f.read_text()
            seed_code(graph, name, 'helper', content)

    # Seed prompts
    prompts_path = a0_path / 'prompts'
    if prompts_path.exists():
        print("\nSeeding prompts...")
        for f in prompts_path.glob('*.md'):
            name = f.stem
            content = f.read_text()
            # Determine category from filename
            if 'system' in name:
                category = 'system'
            elif 'tool' in name:
                category = 'tool'
            elif 'fw.' in name:
                category = 'framework'
            else:
                category = 'other'
            seed_prompt(graph, name, content, category)


def seed_graph(graph, include_a0=True):
    """Main seeding function."""
    print("\n" + "="*60)
    print("  ANYMAKER GRAPH SEEDER")
    print("="*60)

    seed_schema(graph)
    seed_runtime(graph)

    if include_a0:
        seed_from_a0(graph)

    print("\n" + "="*60)
    print("  SEEDING COMPLETE")
    print("="*60 + "\n")


# CLI entry point
if __name__ == '__main__':
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from anymaker.bootstrap import connect_falkordb

    db, graph = connect_falkordb()
    seed_graph(graph)
