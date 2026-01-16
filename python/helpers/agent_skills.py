"""
Agent Skills Integration - Bridges Agent Skills Standard with Agent Zero
Provides lazy-loading, tool/extension integration, and skill execution
"""

from typing import Optional, List, Dict, Any, Type
from pathlib import Path
import importlib.util
import sys

from python.helpers.skill_registry import SkillRegistry, get_registry, Skill
from python.helpers.agents_md_parser import AgentsMdParser
from python.helpers.extension import Extension
from python.helpers.tool import Tool, Response
from python.helpers import extract_tools, files

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from agent import Agent, LoopData


class SkillExtension(Extension):
    """
    Extension that executes an Agent Skill
    Dynamically created from SKILL.md definitions
    """

    def __init__(self, agent: Optional["Agent"], skill: Skill, **kwargs):
        super().__init__(agent, **kwargs)
        self.skill = skill

    async def execute(self, **kwargs) -> Any:
        """
        Execute the skill extension
        Override this in skill-specific implementations
        """
        # Default: Log skill activation
        if self.agent:
            from python.helpers.print_style import PrintStyle
            PrintStyle(font_color="#8E44AD", bold=True).print(
                f"Skill activated: {self.skill.metadata.name}"
            )

        # Skills can provide additional execution logic
        # This is a hook for skill-specific behavior
        return None


class SkillTool(Tool):
    """
    Tool that wraps an Agent Skill
    Allows skills to be invoked as tools in the agent's workflow
    """

    def __init__(
        self,
        agent: "Agent",
        name: str,
        method: str | None,
        args: dict,
        message: str,
        loop_data: "LoopData" | None,
        skill: Skill,
        **kwargs
    ):
        super().__init__(agent, name, method, args, message, loop_data, **kwargs)
        self.skill = skill

    async def execute(self, **kwargs) -> Response:
        """
        Execute the skill as a tool

        Returns:
            Response with skill execution result
        """
        from python.helpers.print_style import PrintStyle

        PrintStyle(font_color="#8E44AD").print(
            f"Executing skill: {self.skill.metadata.name}"
        )
        PrintStyle(font_color="#BB8FCE").print(
            f"Description: {self.skill.metadata.description}"
        )

        # Get skill content
        content = self.skill.content

        # Check if skill has executable scripts
        script_path = self._find_skill_script()

        result_message = f"Skill '{self.skill.metadata.name}' activated.\n\n"
        result_message += f"{self.skill.metadata.description}\n\n"

        if script_path:
            # Execute skill script
            try:
                result = await self._execute_skill_script(script_path)
                result_message += f"Execution result:\n{result}"
            except Exception as e:
                result_message += f"Execution error: {str(e)}"
        else:
            # Provide skill instructions to agent
            result_message += "Instructions:\n" + content

        return Response(
            message=result_message,
            break_loop=False
        )

    def _find_skill_script(self) -> Optional[Path]:
        """
        Find executable script for this skill

        Returns:
            Path to script file or None
        """
        if not self.skill.file_path:
            return None

        skill_dir = self.skill.file_path.parent

        # Look for common script files
        for script_name in ['run.py', 'execute.py', 'main.py', 'skill.py']:
            script_path = skill_dir / script_name
            if script_path.exists():
                return script_path

        return None

    async def _execute_skill_script(self, script_path: Path) -> str:
        """
        Execute a skill's Python script

        Args:
            script_path: Path to the script

        Returns:
            Execution result as string
        """
        try:
            # Import the script as a module
            spec = importlib.util.spec_from_file_location(
                f"skill_{self.skill.metadata.name}",
                script_path
            )

            if spec is None or spec.loader is None:
                return f"Could not load script: {script_path}"

            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)

            # Look for execute() or main() function
            if hasattr(module, 'execute'):
                result = await module.execute(agent=self.agent, args=self.args)
                return str(result)
            elif hasattr(module, 'main'):
                result = await module.main(agent=self.agent, args=self.args)
                return str(result)
            else:
                return "Script loaded but no execute() or main() function found"

        except Exception as e:
            return f"Script execution error: {str(e)}"


class AgentSkillsIntegration:
    """
    Integration layer for Agent Skills in Agent Zero
    Handles skill discovery, loading, and registration as tools/extensions
    """

    def __init__(self, registry: Optional[SkillRegistry] = None):
        """
        Initialize the integration

        Args:
            registry: Optional skill registry (defaults to global)
        """
        self.registry = registry or get_registry()

        # Caches
        self._tool_classes: Dict[str, Type[SkillTool]] = {}
        self._extension_classes: Dict[str, Type[SkillExtension]] = {}

    def discover_and_register(self, force_refresh: bool = False):
        """
        Discover all skills and prepare them for registration

        Args:
            force_refresh: Force rediscovery of skills
        """
        self.registry.discover_skills(force_refresh)

    def get_skill_as_tool(self, skill_name: str, agent: "Agent") -> Optional[Type[Tool]]:
        """
        Get a skill as a Tool class

        Args:
            skill_name: Name of the skill
            agent: Agent instance

        Returns:
            Tool class or None
        """
        # Check cache
        if skill_name in self._tool_classes:
            return self._tool_classes[skill_name]

        # Load skill
        skill = self.registry.get_skill(skill_name)
        if not skill:
            return None

        # Create dynamic tool class
        class DynamicSkillTool(SkillTool):
            def __init__(self, agent_inst, name, method, args, message, loop_data, **kwargs):
                super().__init__(
                    agent_inst, name, method, args, message, loop_data,
                    skill=skill,
                    **kwargs
                )

        # Cache and return
        self._tool_classes[skill_name] = DynamicSkillTool
        return DynamicSkillTool

    def get_skill_as_extension(self, skill_name: str) -> Optional[Type[Extension]]:
        """
        Get a skill as an Extension class

        Args:
            skill_name: Name of the skill

        Returns:
            Extension class or None
        """
        # Check cache
        if skill_name in self._extension_classes:
            return self._extension_classes[skill_name]

        # Load skill
        skill = self.registry.get_skill(skill_name)
        if not skill:
            return None

        # Create dynamic extension class
        class DynamicSkillExtension(SkillExtension):
            def __init__(self, agent, **kwargs):
                super().__init__(agent, skill=skill, **kwargs)

        # Cache and return
        self._extension_classes[skill_name] = DynamicSkillExtension
        return DynamicSkillExtension

    def get_available_skills_for_agent(self, agent: Optional["Agent"] = None) -> List[Dict]:
        """
        Get list of available skills for display/selection

        Args:
            agent: Optional agent for filtering

        Returns:
            List of skill metadata dictionaries
        """
        return self.registry.list_available_skills()

    def get_skills_by_context(self, context: str, agent: Optional["Agent"] = None) -> List[Skill]:
        """
        Get skills relevant to a context/trigger

        Args:
            context: Context or trigger keyword
            agent: Optional agent instance

        Returns:
            List of matching skills
        """
        return self.registry.get_skills_by_trigger(context)

    def load_skill_for_agent(self, skill_name: str, agent: "Agent") -> bool:
        """
        Load a skill for an agent (as tool or extension)

        Args:
            skill_name: Name of the skill
            agent: Agent instance

        Returns:
            True if loaded successfully
        """
        # Get skill
        skill = self.registry.get_skill(skill_name)
        if not skill:
            return False

        # For now, just ensure it's cached
        # Actual registration happens through tool/extension systems
        self.get_skill_as_tool(skill_name, agent)
        self.get_skill_as_extension(skill_name)

        return True

    def search_skills(self, query: str) -> List[Dict]:
        """
        Search for skills

        Args:
            query: Search query

        Returns:
            List of matching skill metadata
        """
        return self.registry.search_skills(query)

    def get_skill_details(self, skill_name: str) -> Optional[Dict]:
        """
        Get detailed information about a skill

        Args:
            skill_name: Name of the skill

        Returns:
            Skill details dictionary or None
        """
        skill = self.registry.get_skill(skill_name)
        if not skill:
            return None

        return skill.to_dict()

    def install_skill_from_path(self, skill_path: Path, target: str = "project") -> bool:
        """
        Install a skill from a path (supports skilz/n-skills installers)

        Args:
            skill_path: Path to skill directory or SKILL.md
            target: Installation target ("project" or "global")

        Returns:
            True if installed successfully
        """
        try:
            # Determine skill file
            if skill_path.is_dir():
                skill_file = skill_path / "SKILL.md"
            else:
                skill_file = skill_path

            if not skill_file.exists():
                print(f"SKILL.md not found in {skill_path}")
                return False

            # Parse skill
            skill = AgentsMdParser.parse_file(skill_file)
            if not skill:
                print(f"Failed to parse skill from {skill_file}")
                return False

            # Determine target directory
            if target == "global":
                target_base = Path.home() / ".config" / "agent-zero" / "skills"
            else:
                target_base = self.registry.project_root / ".agent-zero" / "skills"

            target_dir = target_base / skill.metadata.name

            # Create target directory
            target_dir.mkdir(parents=True, exist_ok=True)

            # Copy skill files
            import shutil

            if skill_path.is_dir():
                # Copy entire directory
                for item in skill_path.iterdir():
                    if item.is_file():
                        shutil.copy2(item, target_dir / item.name)
                    elif item.is_dir():
                        shutil.copytree(item, target_dir / item.name, dirs_exist_ok=True)
            else:
                # Copy just the SKILL.md file
                shutil.copy2(skill_file, target_dir / "SKILL.md")

            print(f"Skill '{skill.metadata.name}' installed to {target_dir}")

            # Refresh registry
            self.registry.refresh()

            return True

        except Exception as e:
            print(f"Error installing skill: {e}")
            return False

    def get_stats(self) -> Dict:
        """
        Get statistics about the skill system

        Returns:
            Statistics dictionary
        """
        return self.registry.get_stats()


# Global integration instance
_global_integration: Optional[AgentSkillsIntegration] = None


def get_integration() -> AgentSkillsIntegration:
    """
    Get the global skills integration instance

    Returns:
        Global AgentSkillsIntegration instance
    """
    global _global_integration

    if _global_integration is None:
        _global_integration = AgentSkillsIntegration()

    return _global_integration


def discover_skills(force_refresh: bool = False):
    """
    Convenience function to discover skills

    Args:
        force_refresh: Force rediscovery
    """
    integration = get_integration()
    integration.discover_and_register(force_refresh)


def get_available_skills() -> List[Dict]:
    """
    Convenience function to get available skills

    Returns:
        List of skill metadata
    """
    integration = get_integration()
    return integration.get_available_skills_for_agent()


def load_skill(skill_name: str, agent: "Agent") -> bool:
    """
    Convenience function to load a skill

    Args:
        skill_name: Name of the skill
        agent: Agent instance

    Returns:
        True if loaded successfully
    """
    integration = get_integration()
    return integration.load_skill_for_agent(skill_name, agent)
