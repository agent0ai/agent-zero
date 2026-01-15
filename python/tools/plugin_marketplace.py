"""
Plugin Marketplace Tool for Agent Zero
Discover, browse, and install plugins from Claude Code marketplaces
"""

import asyncio
from python.helpers.tool import Tool, Response
from python.helpers import files


class PluginMarketplace(Tool):
    """
    Agent Zero tool for plugin marketplace operations.
    Discover, browse, install, and manage plugins from Claude Code marketplaces.
    """

    def __init__(self, agent, name: str, args: dict, message: str, **kwargs):
        super().__init__(agent, name, args, message, **kwargs)

        # Import manager here to avoid circular imports
        from instruments.custom.plugin_marketplace.marketplace_manager import PluginMarketplaceManager

        # Initialize manager
        db_path = files.get_abs_path("./instruments/custom/plugin_marketplace/data/plugin_marketplace.db")
        self.manager = PluginMarketplaceManager(db_path)

    async def execute(self, **kwargs):
        """Execute plugin marketplace action"""

        action = self.args.get("action", "").lower()

        # Route to appropriate action handler
        action_handlers = {
            # Marketplace management
            "add_marketplace": self._add_marketplace,
            "list_marketplaces": self._list_marketplaces,
            "remove_marketplace": self._remove_marketplace,
            "toggle_marketplace": self._toggle_marketplace,

            # Sync operations
            "sync_marketplace": self._sync_marketplace,
            "sync_all": self._sync_all,

            # Plugin discovery
            "search_plugins": self._search_plugins,
            "list_plugins": self._list_plugins,
            "list_popular": self._list_popular,
            "list_trending": self._list_trending,
            "browse_by_tag": self._browse_by_tag,
            "get_plugin_details": self._get_plugin_details,

            # Installation
            "install_plugin": self._install_plugin,
            "uninstall_plugin": self._uninstall_plugin,
            "list_installed": self._list_installed,
            "check_updates": self._check_updates,
            "update_plugin": self._update_plugin,

            # Integration
            "import_to_agent_zero": self._import_to_agent_zero,

            # Statistics
            "get_stats": self._get_stats,
        }

        handler = action_handlers.get(action)
        if handler:
            return await handler()

        return Response(
            message=f"Unknown action: {action}. Available: {', '.join(action_handlers.keys())}",
            break_loop=False
        )

    # ========== Marketplace Management ==========

    async def _add_marketplace(self):
        """Add a new marketplace source"""
        name = self.args.get("name")
        url = self.args.get("url")
        api_endpoint = self.args.get("api_endpoint")
        marketplace_type = self.args.get("type", "community")
        auto_update = self.args.get("auto_update", False)

        if not name or not url:
            return Response(
                message="Error: name and url are required",
                break_loop=False
            )

        result = self.manager.add_marketplace(
            name=name,
            url=url,
            api_endpoint=api_endpoint,
            marketplace_type=marketplace_type,
            auto_update=auto_update
        )

        return Response(
            message=f"## Marketplace Added\n\n**Name:** {result['name']}\n**URL:** {result['url']}\n**Type:** {result['type']}\n\nUse `sync_marketplace` to fetch plugins.",
            break_loop=False
        )

    async def _list_marketplaces(self):
        """List configured marketplaces"""
        enabled_only = self.args.get("enabled_only", False)

        marketplaces = self.manager.list_marketplaces(enabled_only)

        if not marketplaces:
            return Response(
                message="No marketplaces configured.",
                break_loop=False
            )

        lines = ["## Configured Marketplaces\n"]
        for mp in marketplaces:
            status = "✅" if mp['enabled'] else "❌"
            lines.append(f"### {status} {mp['name']} (ID: {mp['marketplace_id']})")
            lines.append(f"- **URL:** {mp['url']}")
            lines.append(f"- **Type:** {mp['type']}")
            lines.append(f"- **Plugins Cached:** {mp.get('plugin_count', 0)}")
            if mp.get('last_synced'):
                lines.append(f"- **Last Synced:** {mp['last_synced']}")
            lines.append("")

        return Response(
            message="\n".join(lines),
            break_loop=False
        )

    async def _remove_marketplace(self):
        """Remove a marketplace"""
        marketplace_id = self.args.get("marketplace_id")

        if not marketplace_id:
            return Response(
                message="Error: marketplace_id is required",
                break_loop=False
            )

        result = self.manager.remove_marketplace(marketplace_id)

        if "error" in result:
            return Response(
                message=f"Error: {result['error']}",
                break_loop=False
            )

        return Response(
            message=f"Marketplace '{result['name']}' removed.",
            break_loop=False
        )

    async def _toggle_marketplace(self):
        """Enable/disable a marketplace"""
        marketplace_id = self.args.get("marketplace_id")
        enabled = self.args.get("enabled", True)

        if not marketplace_id:
            return Response(
                message="Error: marketplace_id is required",
                break_loop=False
            )

        result = self.manager.toggle_marketplace(marketplace_id, enabled)

        status = "enabled" if enabled else "disabled"
        return Response(
            message=f"Marketplace {marketplace_id} {status}.",
            break_loop=False
        )

    # ========== Sync Operations ==========

    async def _sync_marketplace(self):
        """Sync plugins from a marketplace"""
        marketplace_id = self.args.get("marketplace_id")
        name = self.args.get("name")

        if not marketplace_id and not name:
            return Response(
                message="Error: marketplace_id or name is required",
                break_loop=False
            )

        if name and not marketplace_id:
            mp = self.manager.get_marketplace(name=name)
            if mp:
                marketplace_id = mp['marketplace_id']
            else:
                return Response(
                    message=f"Marketplace not found: {name}",
                    break_loop=False
                )

        result = await self.manager.sync_marketplace(marketplace_id)

        if "error" in result:
            return Response(
                message=f"Sync failed: {result['error']}",
                break_loop=False
            )

        return Response(
            message=f"## Sync Complete\n\n**Marketplace:** {result['marketplace']}\n**Plugins Synced:** {result['plugins_synced']}",
            break_loop=False
        )

    async def _sync_all(self):
        """Sync all enabled marketplaces"""
        result = await self.manager.sync_all()

        lines = ["## Sync All Complete\n"]
        lines.append(f"**Marketplaces Synced:** {result['marketplaces_synced']}")
        lines.append(f"**Total Plugins:** {result['total_plugins']}")
        lines.append("")

        for r in result['results']:
            if "error" in r:
                lines.append(f"- ❌ {r['marketplace']}: {r['error']}")
            else:
                lines.append(f"- ✅ {r['marketplace']}: {r.get('plugins_synced', 0)} plugins")

        return Response(
            message="\n".join(lines),
            break_loop=False
        )

    # ========== Plugin Discovery ==========

    async def _search_plugins(self):
        """Search plugins by name/description"""
        query = self.args.get("query")
        marketplace_id = self.args.get("marketplace_id")
        tags = self.args.get("tags")
        limit = self.args.get("limit", 20)

        if not query:
            return Response(
                message="Error: query is required",
                break_loop=False
            )

        plugins = self.manager.search_plugins(query, marketplace_id, tags, limit)

        if not plugins:
            return Response(
                message=f"No plugins found for: {query}",
                break_loop=False
            )

        return Response(
            message=self._format_plugin_list(plugins, f"Search Results: {query}"),
            break_loop=False
        )

    async def _list_plugins(self):
        """List plugins with sorting"""
        marketplace_id = self.args.get("marketplace_id")
        sort_by = self.args.get("sort_by", "downloads")
        limit = self.args.get("limit", 20)
        offset = self.args.get("offset", 0)

        plugins = self.manager.list_plugins(marketplace_id, sort_by, limit, offset)

        if not plugins:
            return Response(
                message="No plugins found. Try syncing marketplaces first.",
                break_loop=False
            )

        return Response(
            message=self._format_plugin_list(plugins, f"Plugins (sorted by {sort_by})"),
            break_loop=False
        )

    async def _list_popular(self):
        """List most downloaded plugins"""
        limit = self.args.get("limit", 20)

        plugins = self.manager.list_popular(limit)

        if not plugins:
            return Response(
                message="No plugins found. Try syncing marketplaces first.",
                break_loop=False
            )

        return Response(
            message=self._format_plugin_list(plugins, "Popular Plugins"),
            break_loop=False
        )

    async def _list_trending(self):
        """List recently updated plugins"""
        limit = self.args.get("limit", 20)

        plugins = self.manager.list_trending(limit)

        if not plugins:
            return Response(
                message="No plugins found.",
                break_loop=False
            )

        return Response(
            message=self._format_plugin_list(plugins, "Trending Plugins"),
            break_loop=False
        )

    async def _browse_by_tag(self):
        """Browse plugins by tag"""
        tag = self.args.get("tag")
        limit = self.args.get("limit", 20)

        if not tag:
            return Response(
                message="Error: tag is required",
                break_loop=False
            )

        plugins = self.manager.browse_by_tag(tag, limit)

        if not plugins:
            return Response(
                message=f"No plugins found with tag: {tag}",
                break_loop=False
            )

        return Response(
            message=self._format_plugin_list(plugins, f"Plugins tagged: {tag}"),
            break_loop=False
        )

    async def _get_plugin_details(self):
        """Get detailed plugin information"""
        identifier = self.args.get("identifier")
        marketplace_id = self.args.get("marketplace_id")

        if not identifier:
            return Response(
                message="Error: identifier is required",
                break_loop=False
            )

        plugin = self.manager.get_plugin_details(identifier, marketplace_id)

        if "error" in plugin:
            return Response(
                message=f"Error: {plugin['error']}",
                break_loop=False
            )

        lines = [f"## Plugin: {plugin['name']}\n"]
        lines.append(f"**Identifier:** {plugin['identifier']}")
        lines.append(f"**Description:** {plugin.get('description', 'N/A')}")
        lines.append(f"**Version:** {plugin.get('version', 'N/A')}")
        lines.append(f"**Author:** {plugin.get('author', 'N/A')}")
        lines.append(f"**Downloads:** {plugin.get('downloads', 0):,}")
        lines.append(f"**Stars:** {plugin.get('stars', 0)}")

        if plugin.get('tags'):
            lines.append(f"**Tags:** {', '.join(plugin['tags'])}")
        if plugin.get('repository'):
            lines.append(f"**Repository:** {plugin['repository']}")
        if plugin.get('license'):
            lines.append(f"**License:** {plugin['license']}")

        lines.append("")
        lines.append(f"**Install:** `{{{{plugin_marketplace(action=\"install_plugin\", identifier=\"{plugin['identifier']}\")}}}}`")

        return Response(
            message="\n".join(lines),
            break_loop=False
        )

    # ========== Installation ==========

    async def _install_plugin(self):
        """Install a plugin from marketplace"""
        identifier = self.args.get("identifier")
        marketplace_id = self.args.get("marketplace_id")
        use_cli = self.args.get("use_cli", True)
        target_path = self.args.get("target_path")

        if not identifier:
            return Response(
                message="Error: identifier is required",
                break_loop=False
            )

        result = self.manager.install_plugin(
            identifier=identifier,
            marketplace_id=marketplace_id,
            use_cli=use_cli,
            target_path=target_path
        )

        if "error" in result:
            return Response(
                message=f"Installation failed: {result['error']}",
                break_loop=False
            )

        lines = ["## Plugin Installed\n"]
        lines.append(f"**Identifier:** {result['identifier']}")
        lines.append(f"**Status:** {result['status']}")
        lines.append(f"**Method:** {result.get('method', 'N/A')}")

        if result.get('local_path'):
            lines.append(f"**Path:** {result['local_path']}")

        lines.append("")
        lines.append("Use `import_to_agent_zero` to import this plugin's skills.")

        return Response(
            message="\n".join(lines),
            break_loop=False
        )

    async def _uninstall_plugin(self):
        """Uninstall a plugin"""
        identifier = self.args.get("identifier")

        if not identifier:
            return Response(
                message="Error: identifier is required",
                break_loop=False
            )

        result = self.manager.uninstall_plugin(identifier)

        if "error" in result:
            return Response(
                message=f"Uninstall failed: {result['error']}",
                break_loop=False
            )

        return Response(
            message=f"Plugin '{identifier}' uninstalled.",
            break_loop=False
        )

    async def _list_installed(self):
        """List installed plugins"""
        installed = self.manager.list_installed()

        if not installed:
            return Response(
                message="No plugins installed.",
                break_loop=False
            )

        lines = ["## Installed Plugins\n"]
        for p in installed:
            import_icon = "✅" if p.get('import_status') == 'imported' else "⏳"
            lines.append(f"- {import_icon} **{p['plugin_identifier']}**")
            lines.append(f"  Version: {p.get('version', 'N/A')}, Installed: {p['installed_at']}")
            if p.get('local_path'):
                lines.append(f"  Path: {p['local_path']}")

        return Response(
            message="\n".join(lines),
            break_loop=False
        )

    async def _check_updates(self):
        """Check for available updates"""
        updates = self.manager.check_updates()

        if not updates:
            return Response(
                message="All plugins are up to date.",
                break_loop=False
            )

        lines = ["## Available Updates\n"]
        for u in updates:
            lines.append(f"- **{u['identifier']}**: {u['installed_version']} → {u['latest_version']}")

        return Response(
            message="\n".join(lines),
            break_loop=False
        )

    async def _update_plugin(self):
        """Update a plugin to latest version"""
        identifier = self.args.get("identifier")

        if not identifier:
            return Response(
                message="Error: identifier is required",
                break_loop=False
            )

        result = self.manager.update_plugin(identifier)

        if "error" in result:
            return Response(
                message=f"Update failed: {result['error']}",
                break_loop=False
            )

        return Response(
            message=f"Plugin '{identifier}' updated to latest version.",
            break_loop=False
        )

    # ========== Integration ==========

    async def _import_to_agent_zero(self):
        """Import installed plugin to Agent Zero via skill_importer"""
        identifier = self.args.get("identifier")

        if not identifier:
            return Response(
                message="Error: identifier is required",
                break_loop=False
            )

        # Get skill_importer manager
        try:
            from instruments.custom.skill_importer.importer_manager import SkillImporterManager
            skill_db_path = files.get_abs_path("./instruments/custom/skill_importer/data/skill_importer.db")
            skill_manager = SkillImporterManager(skill_db_path)

            result = self.manager.import_installed_plugin(identifier, skill_manager)

            if "error" in result:
                return Response(
                    message=f"Import failed: {result['error']}",
                    break_loop=False
                )

            lines = ["## Plugin Imported to Agent Zero\n"]
            lines.append(f"**Plugin:** {result.get('name', identifier)}")
            lines.append(f"**Skills Imported:** {result.get('skills_count', 0)}")
            lines.append(f"**Hooks Imported:** {result.get('hooks_count', 0)}")
            lines.append(f"**Agents Imported:** {result.get('agents_count', 0)}")

            return Response(
                message="\n".join(lines),
                break_loop=False
            )

        except Exception as e:
            return Response(
                message=f"Import failed: {str(e)}",
                break_loop=False
            )

    # ========== Statistics ==========

    async def _get_stats(self):
        """Get marketplace statistics"""
        stats = self.manager.get_stats()

        lines = ["## Marketplace Statistics\n"]
        lines.append(f"**Marketplaces Enabled:** {stats['marketplaces_enabled']}")
        lines.append(f"**Cached Plugins:** {stats['cached_plugins']}")
        lines.append(f"**Installed Plugins:** {stats['installed_plugins']}")

        if stats.get('top_tags'):
            lines.append("")
            lines.append("### Top Tags")
            for tag, count in stats['top_tags'].items():
                lines.append(f"- {tag}: {count}")

        return Response(
            message="\n".join(lines),
            break_loop=False
        )

    # ========== Helpers ==========

    def _format_plugin_list(self, plugins: list, title: str) -> str:
        """Format plugin list for display"""
        lines = [f"## {title}\n"]

        for p in plugins:
            lines.append(f"### {p['name']}")
            lines.append(f"**{p['identifier']}** | ⬇ {p.get('downloads', 0):,} | ★ {p.get('stars', 0)}")
            if p.get('description'):
                lines.append(f"{p['description'][:100]}...")
            if p.get('tags'):
                lines.append(f"Tags: {', '.join(p['tags'][:5])}")
            lines.append("")

        lines.append(f"*{len(plugins)} plugins shown*")
        return "\n".join(lines)
