#!/usr/bin/env python3
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
