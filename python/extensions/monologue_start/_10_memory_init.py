from python.helpers.extension import Extension
from agent import LoopData
from python.helpers import memory
from python.helpers.skills_manager import SkillsManager
from python.helpers import files
from python.helpers.settings import get_settings
import asyncio


class MemoryInit(Extension):

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        db = await memory.Memory.get(self.agent)

        # Initialize SkillsManager if skills are enabled
        # Run in thread pool to avoid blocking
        settings = get_settings()
        if settings.get("skills_enabled", True):
            # Use skills_directories from settings
            skills_dirs = [
                files.get_abs_path("skills", subdir)
                for subdir in settings.get("skills_directories", ["custom", "builtin", "shared"])
            ]

            # Run skill discovery in thread pool to avoid blocking
            manager = SkillsManager.get_instance()
            await asyncio.to_thread(manager.discover_skills, skills_dirs)


   