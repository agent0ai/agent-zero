import os
import shutil
import asyncio

from initialize import initialize
from agent import AgentContext
from python.helpers import files, memory


async def update_knowledge():
    config = initialize()
    context = AgentContext(config)

    inbox_dir = files.get_abs_path("knowledge", "inbox")
    target_dir = os.path.join(memory.get_custom_knowledge_subdir_abs(context.agent0), "main")

    os.makedirs(inbox_dir, exist_ok=True)
    os.makedirs(target_dir, exist_ok=True)

    moved = []
    for fname in os.listdir(inbox_dir):
        src = os.path.join(inbox_dir, fname)
        dest = os.path.join(target_dir, fname)
        if os.path.isfile(src):
            shutil.move(src, dest)
            moved.append(fname)

    if moved:
        await memory.Memory.reload(context.agent0)
        print(f"Imported {len(moved)} file(s) into the knowledge base: {', '.join(moved)}")
    else:
        print("No new files found in inbox directory")


if __name__ == "__main__":
    asyncio.run(update_knowledge())
