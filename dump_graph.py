#!/usr/bin/env python3
"""
Dump FalkorDB graph to JSON file.
Run this locally or from within Railway.
"""

import json
from datetime import datetime

# Connection settings
HOST = 'falkordb-production-641e.up.railway.app'  # or 'falkordb.railway.internal' if running in Railway
PORT = 6379
PASSWORD = '848i4g64jptrctjs'
GRAPH_NAME = 'FalkorDB'

def dump_graph():
    try:
        from falkordb import FalkorDB
    except ImportError:
        print("Installing falkordb...")
        import subprocess
        subprocess.run(['pip', 'install', 'falkordb'], check=True)
        from falkordb import FalkorDB

    print(f"Connecting to {HOST}:{PORT}...")
    db = FalkorDB(host=HOST, port=PORT, password=PASSWORD)
    graph = db.select_graph(GRAPH_NAME)

    print("Connected. Querying nodes...")

    # Export all nodes with labels
    nodes_query = """
    MATCH (n)
    RETURN ID(n) as id, labels(n) as labels, properties(n) as props
    """
    nodes_result = graph.query(nodes_query)

    nodes = []
    for record in nodes_result.result_set:
        nodes.append({
            'id': record[0],
            'labels': record[1],
            'properties': record[2]
        })

    print(f"Found {len(nodes)} nodes")

    # Export all relationships
    print("Querying relationships...")
    rels_query = """
    MATCH (a)-[r]->(b)
    RETURN ID(a) as from_id, ID(r) as rel_id, type(r) as type, properties(r) as props, ID(b) as to_id
    """
    rels_result = graph.query(rels_query)

    relationships = []
    for record in rels_result.result_set:
        relationships.append({
            'from_id': record[0],
            'rel_id': record[1],
            'type': record[2],
            'properties': record[3],
            'to_id': record[4]
        })

    print(f"Found {len(relationships)} relationships")

    # Build export
    export = {
        'exported_at': datetime.now().isoformat(),
        'source': {
            'host': HOST,
            'graph': GRAPH_NAME
        },
        'nodes': nodes,
        'relationships': relationships
    }

    # Save
    filename = f'graph_dump_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(filename, 'w') as f:
        json.dump(export, f, indent=2, default=str)

    print(f"\nExported to: {filename}")
    print(f"  Nodes: {len(nodes)}")
    print(f"  Relationships: {len(relationships)}")

    return filename

if __name__ == '__main__':
    dump_graph()
