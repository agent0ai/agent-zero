#!/usr/bin/env python3
"""
Anymaker Bootstrap

The ONLY file deployed to Railway.
Connects to FalkorDB, loads runtime from graph, executes.
"""

import os
import sys

# -----------------------------------------------------------------------------
# Configuration from environment
# -----------------------------------------------------------------------------

FALKORDB_HOST = os.getenv("FALKORDB_HOST", "falkordb.railway.internal")
FALKORDB_PORT = int(os.getenv("FALKORDB_PORT", "6379"))
FALKORDB_PASSWORD = os.getenv("FALKORDB_PASSWORD", "")
GRAPH_NAME = os.getenv("GRAPH_NAME", "anymaker")

API_PORT = int(os.getenv("PORT", os.getenv("API_PORT", "8080")))
A0_GUI_PORT = int(os.getenv("A0_GUI_PORT", "8081"))

# -----------------------------------------------------------------------------
# Bootstrap
# -----------------------------------------------------------------------------

def connect_falkordb():
    """Connect to FalkorDB and return graph handle."""
    from falkordb import FalkorDB

    print(f"Connecting to FalkorDB at {FALKORDB_HOST}:{FALKORDB_PORT}...")

    db = FalkorDB(
        host=FALKORDB_HOST,
        port=FALKORDB_PORT,
        password=FALKORDB_PASSWORD if FALKORDB_PASSWORD else None
    )

    graph = db.select_graph(GRAPH_NAME)
    print(f"Connected to graph: {GRAPH_NAME}")

    return db, graph


def check_runtime_exists(graph):
    """Check if Anymaker runtime code exists in graph."""
    result = graph.query("""
        MATCH (c:Code {name: 'runtime', type: 'core'})
        RETURN c.content_hash as hash
    """)
    return len(result.result_set) > 0


def load_and_execute_runtime(graph):
    """Load runtime code from graph and execute."""
    result = graph.query("""
        MATCH (c:Code {name: 'runtime', type: 'core', is_current: true})
        RETURN c.content as content
    """)

    if not result.result_set:
        raise RuntimeError("Runtime code not found in graph")

    runtime_code = result.result_set[0][0]

    print("Executing runtime from graph...")

    # Execute in current namespace, passing graph connection
    exec_globals = {
        '__name__': '__main__',
        '__builtins__': __builtins__,
        'graph': graph,
        'FALKORDB_HOST': FALKORDB_HOST,
        'FALKORDB_PORT': FALKORDB_PORT,
        'FALKORDB_PASSWORD': FALKORDB_PASSWORD,
        'GRAPH_NAME': GRAPH_NAME,
        'API_PORT': API_PORT,
        'A0_GUI_PORT': A0_GUI_PORT,
    }

    exec(runtime_code, exec_globals)


def seed_mode(graph):
    """First-time setup: seed graph with Anymaker code."""
    print("\n" + "="*60)
    print("SEED MODE: Runtime not found in graph")
    print("="*60)
    print("\nRun the seed script to populate the graph:")
    print("  python -m anymaker.seed")
    print("\nOr set ANYMAKER_SEED=1 to auto-seed from this bootstrap")
    print("="*60 + "\n")

    if os.getenv("ANYMAKER_SEED") == "1":
        print("Auto-seeding enabled...")
        from anymaker.seed import seed_graph
        seed_graph(graph)
        return True

    return False


def main():
    print("\n" + "="*60)
    print("  ANYMAKER BOOTSTRAP")
    print("="*60 + "\n")

    # Connect to FalkorDB
    db, graph = connect_falkordb()

    # Check if runtime exists
    if check_runtime_exists(graph):
        print("Runtime found in graph. Loading...")
        load_and_execute_runtime(graph)
    else:
        # Seed mode
        if seed_mode(graph):
            # Retry after seeding
            print("\nSeeding complete. Loading runtime...")
            load_and_execute_runtime(graph)
        else:
            print("Exiting. Please seed the graph first.")
            sys.exit(1)


if __name__ == "__main__":
    main()
