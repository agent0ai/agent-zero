#!/usr/bin/env python3
'''Quick search interface for the integrated knowledge system'''
import asyncio
import sys
sys.path.insert(0, '.')
from integrated_knowledge_system import IntegratedKnowledgeSystem

async def search():
    system = IntegratedKnowledgeSystem()
    await system.setup()

    while True:
        query = input("\nEnter search query (or 'quit'): ")
        if query.lower() == 'quit':
            break

        results = await system.search_all_collections(query, k=3)

        for collection, data in results.items():
            if data["count"] > 0:
                print(f"\n[{collection}] ({data['count']} results):")
                for i, result in enumerate(data["results"], 1):
                    print(f"  {i}. {result.page_content[:150]}...")

if __name__ == "__main__":
    print("Integrated Knowledge Search Interface")
    print("="*40)
    asyncio.run(search())
