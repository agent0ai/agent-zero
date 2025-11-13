import asyncio
import aiohttp
import json
from typing import Dict, List, Any, Optional
from python.helpers.tool import Tool, Response
from python.helpers.print_style import PrintStyle
from python.helpers.errors import handle_error


class WordPressAPI(Tool):
    """
    Tool for interacting with WordPress REST API to fetch site data, posts, pages, and metadata.
    Supports both public and authenticated API access.
    """

    async def execute(self, **kwargs):
        action = self.args.get("action", "").lower().strip()
        site_url = self.args.get("site_url", "").strip()

        if not site_url:
            return Response(
                message="Error: site_url is required. Please provide the WordPress site URL.",
                break_loop=False
            )

        # Ensure site_url has protocol
        if not site_url.startswith(("http://", "https://")):
            site_url = "https://" + site_url

        try:
            if action == "get_posts":
                response = await self.get_posts(site_url)
            elif action == "get_pages":
                response = await self.get_pages(site_url)
            elif action == "get_post":
                post_id = self.args.get("post_id")
                response = await self.get_post(site_url, post_id)
            elif action == "get_site_info":
                response = await self.get_site_info(site_url)
            elif action == "get_media":
                response = await self.get_media(site_url)
            elif action == "get_categories":
                response = await self.get_categories(site_url)
            elif action == "get_tags":
                response = await self.get_tags(site_url)
            elif action == "search_content":
                search_query = self.args.get("search_query", "")
                response = await self.search_content(site_url, search_query)
            else:
                response = f"Unknown action: {action}\n\nAvailable actions:\n- get_site_info\n- get_posts\n- get_pages\n- get_post\n- get_media\n- get_categories\n- get_tags\n- search_content"

            return Response(message=response, break_loop=False)

        except Exception as e:
            error_msg = f"WordPress API Error: {str(e)}"
            handle_error(e)
            return Response(message=error_msg, break_loop=False)

    async def make_wp_request(
        self,
        site_url: str,
        endpoint: str,
        params: Optional[Dict] = None,
        auth: Optional[tuple] = None
    ) -> Any:
        """Make an HTTP request to WordPress REST API"""
        url = f"{site_url.rstrip('/')}/wp-json/wp/v2/{endpoint}"

        # Get auth credentials from agent memory/config if available
        if not auth:
            username = self.agent.get_data("wp_username")
            password = self.agent.get_data("wp_app_password")
            if username and password:
                auth = aiohttp.BasicAuth(username, password)

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, auth=auth, timeout=30) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    error_text = await resp.text()
                    raise Exception(f"HTTP {resp.status}: {error_text}")

    async def get_site_info(self, site_url: str) -> str:
        """Fetch WordPress site information"""
        try:
            # Get site info from root endpoint
            url = f"{site_url.rstrip('/')}/wp-json"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as resp:
                    data = await resp.json()

            info = {
                "name": data.get("name", "N/A"),
                "description": data.get("description", "N/A"),
                "url": data.get("url", "N/A"),
                "home": data.get("home", "N/A"),
                "gmt_offset": data.get("gmt_offset", "N/A"),
                "timezone_string": data.get("timezone_string", "N/A"),
            }

            return json.dumps(info, indent=2)
        except Exception as e:
            return f"Failed to fetch site info: {str(e)}"

    async def get_posts(self, site_url: str, per_page: int = 10) -> str:
        """Fetch WordPress posts with SEO-relevant data"""
        try:
            params = {
                "per_page": min(per_page, 100),
                "_embed": "true"  # Include embedded data like featured images
            }
            posts = await self.make_wp_request(site_url, "posts", params)

            result = []
            for post in posts:
                post_data = {
                    "id": post.get("id"),
                    "title": post.get("title", {}).get("rendered", ""),
                    "slug": post.get("slug", ""),
                    "link": post.get("link", ""),
                    "excerpt": post.get("excerpt", {}).get("rendered", "")[:200],
                    "status": post.get("status", ""),
                    "date": post.get("date", ""),
                    "modified": post.get("modified", ""),
                    "categories": post.get("categories", []),
                    "tags": post.get("tags", []),
                }

                # Try to get Yoast SEO data if available
                if "yoast_head_json" in post:
                    yoast = post["yoast_head_json"]
                    post_data["seo"] = {
                        "title": yoast.get("title", ""),
                        "description": yoast.get("description", ""),
                        "canonical": yoast.get("canonical", ""),
                        "og_title": yoast.get("og_title", ""),
                        "og_description": yoast.get("og_description", ""),
                    }

                result.append(post_data)

            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Failed to fetch posts: {str(e)}"

    async def get_pages(self, site_url: str, per_page: int = 10) -> str:
        """Fetch WordPress pages"""
        try:
            params = {"per_page": min(per_page, 100)}
            pages = await self.make_wp_request(site_url, "pages", params)

            result = []
            for page in pages:
                page_data = {
                    "id": page.get("id"),
                    "title": page.get("title", {}).get("rendered", ""),
                    "slug": page.get("slug", ""),
                    "link": page.get("link", ""),
                    "status": page.get("status", ""),
                    "parent": page.get("parent", 0),
                }
                result.append(page_data)

            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Failed to fetch pages: {str(e)}"

    async def get_post(self, site_url: str, post_id: str) -> str:
        """Fetch a specific post with full content and SEO data"""
        try:
            post = await self.make_wp_request(site_url, f"posts/{post_id}")

            post_data = {
                "id": post.get("id"),
                "title": post.get("title", {}).get("rendered", ""),
                "content": post.get("content", {}).get("rendered", ""),
                "excerpt": post.get("excerpt", {}).get("rendered", ""),
                "slug": post.get("slug", ""),
                "link": post.get("link", ""),
                "status": post.get("status", ""),
                "date": post.get("date", ""),
                "modified": post.get("modified", ""),
                "categories": post.get("categories", []),
                "tags": post.get("tags", []),
            }

            if "yoast_head_json" in post:
                post_data["seo"] = post["yoast_head_json"]

            return json.dumps(post_data, indent=2)
        except Exception as e:
            return f"Failed to fetch post: {str(e)}"

    async def get_categories(self, site_url: str) -> str:
        """Fetch all categories"""
        try:
            categories = await self.make_wp_request(site_url, "categories", {"per_page": 100})
            result = [{"id": cat["id"], "name": cat["name"], "slug": cat["slug"], "count": cat["count"]}
                     for cat in categories]
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Failed to fetch categories: {str(e)}"

    async def get_tags(self, site_url: str) -> str:
        """Fetch all tags"""
        try:
            tags = await self.make_wp_request(site_url, "tags", {"per_page": 100})
            result = [{"id": tag["id"], "name": tag["name"], "slug": tag["slug"], "count": tag["count"]}
                     for tag in tags]
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Failed to fetch tags: {str(e)}"

    async def get_media(self, site_url: str, per_page: int = 20) -> str:
        """Fetch media items to check alt text and SEO optimization"""
        try:
            params = {"per_page": min(per_page, 100)}
            media = await self.make_wp_request(site_url, "media", params)

            result = []
            for item in media:
                media_data = {
                    "id": item.get("id"),
                    "title": item.get("title", {}).get("rendered", ""),
                    "alt_text": item.get("alt_text", ""),
                    "caption": item.get("caption", {}).get("rendered", ""),
                    "source_url": item.get("source_url", ""),
                    "mime_type": item.get("mime_type", ""),
                }
                result.append(media_data)

            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Failed to fetch media: {str(e)}"

    async def search_content(self, site_url: str, search_query: str) -> str:
        """Search WordPress content"""
        try:
            params = {"search": search_query, "per_page": 20}
            results = await self.make_wp_request(site_url, "search", params)

            formatted = []
            for item in results:
                formatted.append({
                    "id": item.get("id"),
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "type": item.get("type", ""),
                    "subtype": item.get("subtype", ""),
                })

            return json.dumps(formatted, indent=2)
        except Exception as e:
            return f"Failed to search content: {str(e)}"
