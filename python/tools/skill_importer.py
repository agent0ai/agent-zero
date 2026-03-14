"""
Skill Importer Tool for Agent Jumbo
Import Claude Code plugin skills, hooks, agents, and MCP servers
"""

import json

from python.helpers import files
from python.helpers.tool import Response, Tool


class SkillImporter(Tool):
    """
    Agent Jumbo tool for importing Claude Code plugins and skills.
    Enables conversion of Claude Code ecosystem components to Agent Jumbo tools.
    """

    def __init__(self, agent, name: str, method: str | None, args: dict, message: str, loop_data=None, **kwargs):
        super().__init__(agent, name, method, args, message, loop_data, **kwargs)

        # Import manager here to avoid circular imports
        from instruments.custom.skill_importer.importer_manager import SkillImporterManager

        # Initialize manager
        db_path = files.get_abs_path("./instruments/custom/skill_importer/data/skill_importer.db")
        self.manager = SkillImporterManager(db_path)

    async def execute(self, **kwargs):
        """Execute skill importer action"""

        action = self.args.get("action", "").lower()

        # Route to appropriate action handler
        action_handlers = {
            # Skill actions
            "import_skill": self._import_skill,
            "list_skills": self._list_skills,
            "get_skill": self._get_skill,
            "remove_skill": self._remove_skill,
            "toggle_skill": self._toggle_skill,
            "generate_prompt": self._generate_prompt,
            "get_skill_context": self._get_skill_context,
            # Plugin actions
            "import_plugin": self._import_plugin,
            "list_plugins": self._list_plugins,
            "get_plugin": self._get_plugin,
            "remove_plugin": self._remove_plugin,
            "get_mcp_config": self._get_mcp_config,
            # Bulk operations
            "sync_directory": self._sync_directory,
            # Statistics
            "get_stats": self._get_stats,
        }

        handler = action_handlers.get(action)
        if handler:
            return await handler()

        return Response(
            message=f"Unknown action: {action}. Available: {', '.join(action_handlers.keys())}", break_loop=False
        )

    # ========== Skill Actions ==========

    async def _import_skill(self):
        """Import a single skill from a file"""
        source_path = self.args.get("source_path")
        category = self.args.get("category")

        if not source_path:
            return Response(message="Error: source_path is required", break_loop=False)

        result = self.manager.import_skill(source_path, category=category)
        return Response(message=self._format_result(result, "Skill Import"), break_loop=False)

    async def _list_skills(self):
        """List all imported skills"""
        enabled_only = self.args.get("enabled_only", True)
        category = self.args.get("category")
        plugin_name = self.args.get("plugin_name")

        skills = self.manager.list_skills(enabled_only=enabled_only, category=category, plugin_name=plugin_name)

        if not skills:
            return Response(message="No skills found.", break_loop=False)

        # Format skill list
        lines = ["## Imported Skills\n"]
        for skill in skills:
            status = "enabled" if skill.get("enabled") else "disabled"
            lines.append(f"- **{skill['name']}** (ID: {skill['skill_id']}) [{status}]")
            if skill.get("description"):
                lines.append(f"  {skill['description'][:100]}...")
            if skill.get("plugin_name"):
                lines.append(f"  Plugin: {skill['plugin_name']}")

        lines.append(f"\nTotal: {len(skills)} skills")

        return Response(message="\n".join(lines), break_loop=False)

    async def _get_skill(self):
        """Get details of a specific skill"""
        skill_id = self.args.get("skill_id")
        name = self.args.get("name")

        if not skill_id and not name:
            return Response(message="Error: skill_id or name is required", break_loop=False)

        skill = self.manager.get_skill(name=name, skill_id=skill_id)
        if not skill:
            return Response(message=f"Skill not found: {skill_id or name}", break_loop=False)

        return Response(message=self._format_result(skill, f"Skill: {skill['name']}"), break_loop=False)

    async def _remove_skill(self):
        """Remove an imported skill"""
        skill_id = self.args.get("skill_id")

        if not skill_id:
            return Response(message="Error: skill_id is required", break_loop=False)

        result = self.manager.remove_skill(skill_id)
        return Response(message=self._format_result(result, "Remove Skill"), break_loop=False)

    async def _toggle_skill(self):
        """Enable or disable a skill"""
        skill_id = self.args.get("skill_id")
        enabled = self.args.get("enabled", True)

        if not skill_id:
            return Response(message="Error: skill_id is required", break_loop=False)

        self.manager.toggle_skill(skill_id, enabled)
        status = "enabled" if enabled else "disabled"
        return Response(message=f"Skill {skill_id} {status}.", break_loop=False)

    async def _generate_prompt(self):
        """Generate Agent Jumbo tool prompt for a skill"""
        skill_id = self.args.get("skill_id")

        if not skill_id:
            return Response(message="Error: skill_id is required", break_loop=False)

        prompt = self.manager.generate_tool_prompt(skill_id)
        if not prompt:
            return Response(message=f"Could not generate prompt for skill {skill_id}", break_loop=False)

        return Response(message=f"## Generated Tool Prompt\n\n{prompt}", break_loop=False)

    async def _get_skill_context(self):
        """Get execution context for a skill"""
        skill_id = self.args.get("skill_id")

        if not skill_id:
            return Response(message="Error: skill_id is required", break_loop=False)

        context = self.manager.get_execution_context(skill_id)
        return Response(message=self._format_result(context, "Skill Execution Context"), break_loop=False)

    # ========== Plugin Actions ==========

    async def _import_plugin(self):
        """Import a complete Claude Code plugin"""
        plugin_path = self.args.get("plugin_path")

        if not plugin_path:
            return Response(message="Error: plugin_path is required", break_loop=False)

        result = self.manager.import_plugin(plugin_path)

        # Format summary
        if "error" in result:
            return Response(message=f"Error importing plugin: {result['error']}", break_loop=False)

        lines = [f"## Plugin Imported: {result['plugin_name']}\n"]
        lines.append(f"**Plugin ID:** {result['plugin_id']}")

        if result["skills"]:
            lines.append(f"\n### Skills ({len(result['skills'])})")
            for s in result["skills"][:5]:
                lines.append(f"- {s.get('name', s.get('file', 'Unknown'))}")
            if len(result["skills"]) > 5:
                lines.append(f"  ... and {len(result['skills']) - 5} more")

        if result["hooks"]:
            lines.append(f"\n### Hooks ({len(result['hooks'])})")
            for h in result["hooks"]:
                lines.append(f"- {h.get('name')} ({h.get('event')})")

        if result["agents"]:
            lines.append(f"\n### Agents ({len(result['agents'])})")
            for a in result["agents"]:
                lines.append(f"- {a.get('name')}: {a.get('description', '')[:50]}")

        if result["mcp_servers"]:
            lines.append(f"\n### MCP Servers ({len(result['mcp_servers'])})")
            for m in result["mcp_servers"]:
                lines.append(f"- {m.get('name')} ({m.get('type')})")

        lines.append(f"\n**Total Components:** {result['summary']['total_components']}")

        return Response(message="\n".join(lines), break_loop=False)

    async def _list_plugins(self):
        """List all imported plugins"""
        enabled_only = self.args.get("enabled_only", True)

        plugins = self.manager.list_plugins(enabled_only=enabled_only)

        if not plugins:
            return Response(message="No plugins imported yet.", break_loop=False)

        lines = ["## Imported Plugins\n"]
        for plugin in plugins:
            status = "enabled" if plugin.get("enabled") else "disabled"
            lines.append(f"### {plugin['name']} (ID: {plugin['plugin_id']}) [{status}]")
            if plugin.get("description"):
                lines.append(f"{plugin['description']}")
            lines.append(f"- Skills: {plugin.get('skills_count', 0)}")
            lines.append(f"- Hooks: {plugin.get('hooks_count', 0)}")
            lines.append(f"- Agents: {plugin.get('agents_count', 0)}")
            lines.append(f"- MCP Servers: {plugin.get('mcp_servers_count', 0)}")
            lines.append("")

        return Response(message="\n".join(lines), break_loop=False)

    async def _get_plugin(self):
        """Get details of a specific plugin"""
        plugin_id = self.args.get("plugin_id")
        name = self.args.get("name")

        if not plugin_id and not name:
            return Response(message="Error: plugin_id or name is required", break_loop=False)

        plugin = self.manager.get_plugin(name=name, plugin_id=plugin_id)
        if not plugin:
            return Response(message=f"Plugin not found: {plugin_id or name}", break_loop=False)

        return Response(message=self._format_result(plugin, f"Plugin: {plugin['name']}"), break_loop=False)

    async def _remove_plugin(self):
        """Remove a plugin and all its components"""
        plugin_id = self.args.get("plugin_id")

        if not plugin_id:
            return Response(message="Error: plugin_id is required", break_loop=False)

        result = self.manager.remove_plugin(plugin_id)
        return Response(message=self._format_result(result, "Remove Plugin"), break_loop=False)

    async def _get_mcp_config(self):
        """Get MCP configuration for Agent Jumbo integration"""
        plugin_id = self.args.get("plugin_id")

        if not plugin_id:
            return Response(message="Error: plugin_id is required", break_loop=False)

        config = self.manager.get_plugin_mcp_config(plugin_id)

        if not config.get("mcpServers"):
            return Response(message="No MCP servers configured for this plugin.", break_loop=False)

        config_json = json.dumps(config, indent=2)
        return Response(
            message=f"## MCP Configuration\n\nAdd this to your Agent Jumbo MCP settings:\n\n```json\n{config_json}\n```",
            break_loop=False,
        )

    # ========== Bulk Operations ==========

    async def _sync_directory(self):
        """Bulk import skills from a directory"""
        directory = self.args.get("directory")
        recursive = self.args.get("recursive", True)

        if not directory:
            return Response(message="Error: directory is required", break_loop=False)

        result = self.manager.sync_plugins_directory(directory, recursive=recursive)

        if "error" in result:
            return Response(message=f"Error: {result['error']}", break_loop=False)

        lines = ["## Directory Sync Results\n"]
        lines.append(f"**Directory:** {directory}")
        lines.append(f"**Files Found:** {result['summary']['total_found']}")
        lines.append(f"**Imported:** {result['summary']['imported']}")
        lines.append(f"**Failed:** {result['summary']['failed']}")

        if result["imported"]:
            lines.append("\n### Imported Skills")
            for skill in result["imported"][:10]:
                lines.append(f"- {skill.get('name')}")
            if len(result["imported"]) > 10:
                lines.append(f"  ... and {len(result['imported']) - 10} more")

        if result["failed"]:
            lines.append("\n### Failed Imports")
            for fail in result["failed"][:5]:
                lines.append(f"- {fail.get('file')}: {fail.get('error')}")

        return Response(message="\n".join(lines), break_loop=False)

    # ========== Statistics ==========

    async def _get_stats(self):
        """Get execution statistics"""
        skill_id = self.args.get("skill_id")

        stats = self.manager.get_stats(skill_id)

        return Response(message=self._format_result(stats, "Execution Statistics"), break_loop=False)

    # ========== Helpers ==========

    def _format_result(self, data: dict, title: str) -> str:
        """Format result dictionary as readable output"""
        lines = [f"## {title}\n"]

        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    lines.append(f"**{key}:**")
                    for k, v in value.items():
                        lines.append(f"  - {k}: {v}")
                elif isinstance(value, list):
                    lines.append(f"**{key}:** ({len(value)} items)")
                    for item in value[:5]:
                        if isinstance(item, dict):
                            lines.append(f"  - {item.get('name', item)}")
                        else:
                            lines.append(f"  - {item}")
                    if len(value) > 5:
                        lines.append(f"  ... and {len(value) - 5} more")
                else:
                    lines.append(f"**{key}:** {value}")
        else:
            lines.append(str(data))

        return "\n".join(lines)
