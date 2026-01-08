import asyncio
import aiohttp
import json
from typing import Dict, Any, Optional
from python.helpers.tool import Tool, Response
from python.helpers.print_style import PrintStyle
from python.helpers.errors import handle_error


class WordPressSEOManager(Tool):
    """
    Tool for managing WordPress SEO metadata and content optimization.
    Requires WordPress Application Password for authentication.
    ALWAYS confirm with user before making changes.
    """

    async def execute(self, **kwargs):
        action = self.args.get("action", "").lower().strip()
        site_url = self.args.get("site_url", "").strip()
        confirmed = self.args.get("confirmed", "false").lower() == "true"

        if not site_url:
            return Response(
                message="Error: site_url is required.",
                break_loop=False
            )

        # Ensure site_url has protocol
        if not site_url.startswith(("http://", "https://")):
            site_url = "https://" + site_url

        # Safety check: require confirmation for write operations
        write_actions = ["update_post", "update_meta", "bulk_update_alt_text", "update_yoast_meta"]
        if action in write_actions and not confirmed:
            return Response(
                message=f"⚠️ CONFIRMATION REQUIRED ⚠️\n\nYou are about to modify WordPress content with action: {action}\n\nThis will make changes to your live WordPress site.\n\nPlease review the changes and set 'confirmed': 'true' in tool_args to proceed.\n\nProposed changes:\n{json.dumps(self.args, indent=2)}",
                break_loop=False
            )

        try:
            if action == "update_post_meta":
                response = await self.update_post_meta(site_url)
            elif action == "update_post_content":
                response = await self.update_post_content(site_url)
            elif action == "bulk_update_alt_text":
                response = await self.bulk_update_alt_text(site_url)
            elif action == "update_categories":
                response = await self.update_categories(site_url)
            elif action == "update_tags":
                response = await self.update_tags(site_url)
            else:
                response = f"Unknown action: {action}\n\nAvailable actions:\n- update_post_meta (update title, excerpt, slug)\n- update_post_content (update post content)\n- bulk_update_alt_text (update image alt text)\n- update_categories (assign categories to post)\n- update_tags (assign tags to post)\n\n⚠️ All actions require 'confirmed': 'true' to execute"

            return Response(message=response, break_loop=False)

        except Exception as e:
            error_msg = f"WordPress SEO Manager Error: {str(e)}"
            handle_error(e)
            return Response(message=error_msg, break_loop=False)

    async def get_auth(self) -> Optional[aiohttp.BasicAuth]:
        """Get WordPress authentication credentials"""
        username = self.agent.get_data("wp_username")
        password = self.agent.get_data("wp_app_password")

        if not username or not password:
            raise Exception(
                "WordPress credentials not found. Please provide:\n"
                "- wp_username: WordPress username\n"
                "- wp_app_password: WordPress Application Password\n"
                "Store these using memory_save tool."
            )

        return aiohttp.BasicAuth(username, password)

    async def make_wp_post_request(
        self,
        site_url: str,
        endpoint: str,
        data: Dict,
        method: str = "POST"
    ) -> Any:
        """Make an HTTP POST/PUT request to WordPress REST API"""
        url = f"{site_url.rstrip('/')}/wp-json/wp/v2/{endpoint}"
        auth = await self.get_auth()

        async with aiohttp.ClientSession() as session:
            if method == "POST":
                request_func = session.post
            elif method == "PUT":
                request_func = session.put
            else:
                raise ValueError(f"Unsupported method: {method}")

            async with request_func(
                url,
                json=data,
                auth=auth,
                timeout=30,
                headers={"Content-Type": "application/json"}
            ) as resp:
                if resp.status in [200, 201]:
                    return await resp.json()
                else:
                    error_text = await resp.text()
                    raise Exception(f"HTTP {resp.status}: {error_text}")

    async def update_post_meta(self, site_url: str) -> str:
        """Update post metadata (title, excerpt, slug)"""
        try:
            post_id = self.args.get("post_id")
            if not post_id:
                return "Error: post_id is required"

            update_data = {}

            # Update title if provided
            if "title" in self.args:
                update_data["title"] = self.args["title"]

            # Update excerpt (meta description) if provided
            if "excerpt" in self.args:
                update_data["excerpt"] = self.args["excerpt"]

            # Update slug if provided
            if "slug" in self.args:
                update_data["slug"] = self.args["slug"]

            if not update_data:
                return "Error: No update data provided. Specify title, excerpt, or slug."

            result = await self.make_wp_post_request(
                site_url,
                f"posts/{post_id}",
                update_data,
                method="POST"
            )

            return f"✅ Successfully updated post {post_id}\n\nUpdated fields:\n{json.dumps(update_data, indent=2)}\n\nResult:\n{json.dumps(result, indent=2)}"

        except Exception as e:
            return f"Failed to update post meta: {str(e)}"

    async def update_post_content(self, site_url: str) -> str:
        """Update post content"""
        try:
            post_id = self.args.get("post_id")
            content = self.args.get("content")

            if not post_id or not content:
                return "Error: post_id and content are required"

            update_data = {"content": content}

            result = await self.make_wp_post_request(
                site_url,
                f"posts/{post_id}",
                update_data,
                method="POST"
            )

            return f"✅ Successfully updated post content for post {post_id}\n\nContent length: {len(content)} characters"

        except Exception as e:
            return f"Failed to update post content: {str(e)}"

    async def update_categories(self, site_url: str) -> str:
        """Update post categories"""
        try:
            post_id = self.args.get("post_id")
            categories = self.args.get("categories", [])

            if not post_id:
                return "Error: post_id is required"

            if not isinstance(categories, list):
                return "Error: categories must be a list of category IDs"

            update_data = {"categories": categories}

            result = await self.make_wp_post_request(
                site_url,
                f"posts/{post_id}",
                update_data,
                method="POST"
            )

            return f"✅ Successfully updated categories for post {post_id}\n\nCategories: {categories}"

        except Exception as e:
            return f"Failed to update categories: {str(e)}"

    async def update_tags(self, site_url: str) -> str:
        """Update post tags"""
        try:
            post_id = self.args.get("post_id")
            tags = self.args.get("tags", [])

            if not post_id:
                return "Error: post_id is required"

            if not isinstance(tags, list):
                return "Error: tags must be a list of tag IDs"

            update_data = {"tags": tags}

            result = await self.make_wp_post_request(
                site_url,
                f"posts/{post_id}",
                update_data,
                method="POST"
            )

            return f"✅ Successfully updated tags for post {post_id}\n\nTags: {tags}"

        except Exception as e:
            return f"Failed to update tags: {str(e)}"

    async def bulk_update_alt_text(self, site_url: str) -> str:
        """Bulk update alt text for media items"""
        try:
            updates = self.args.get("media_updates", [])

            if not isinstance(updates, list):
                return "Error: media_updates must be a list of {media_id, alt_text} objects"

            results = []
            for update in updates:
                media_id = update.get("media_id")
                alt_text = update.get("alt_text")

                if not media_id or not alt_text:
                    results.append(f"❌ Skipped: missing media_id or alt_text")
                    continue

                try:
                    result = await self.make_wp_post_request(
                        site_url,
                        f"media/{media_id}",
                        {"alt_text": alt_text},
                        method="POST"
                    )
                    results.append(f"✅ Updated media {media_id} with alt text: {alt_text}")
                except Exception as e:
                    results.append(f"❌ Failed to update media {media_id}: {str(e)}")

            return "\n".join(results)

        except Exception as e:
            return f"Failed bulk alt text update: {str(e)}"
