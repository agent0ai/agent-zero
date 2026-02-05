"""
Olostep Tool for Agent Zero

This tool provides web scraping, search, and data extraction capabilities
through the Olostep API. It allows agents to:
- Scrape any URL and get clean markdown, HTML, or structured data
- Search the web and get AI-powered answers with sources
- Map websites to discover all URLs
- Perform Google searches with structured results
"""

from python.helpers.tool import Tool, Response
from python.helpers.print_style import PrintStyle
from python.helpers import olostep_api
from python.helpers.errors import handle_error


class Olostep(Tool):
    """
    Olostep integration tool for Agent Zero.
    
    Supported methods:
    - scrape: Extract content from any URL (markdown, HTML, text, JSON)
    - search: Search the web and get AI-powered answers
    - google: Perform Google searches with structured results
    - map: Discover all URLs on a website
    """
    
    async def execute(self, **kwargs) -> Response:
        method = self.method or "scrape"
        
        try:
            if method == "scrape":
                return await self._scrape()
            elif method == "search" or method == "answer":
                return await self._search()
            elif method == "google":
                return await self._google_search()
            elif method == "map":
                return await self._map_website()
            else:
                return Response(
                    message=f"Unknown method '{method}'. Available methods: scrape, search, google, map",
                    break_loop=False,
                )
        except Exception as e:
            handle_error(e)
            return Response(
                message=f"Olostep error: {str(e)}",
                break_loop=False,
            )
    
    async def _scrape(self) -> Response:
        """Scrape a URL and return its content."""
        url = self.args.get("url", "")
        if not url:
            return Response(
                message="Error: 'url' argument is required for scraping",
                break_loop=False,
            )
        
        # Parse formats - default to markdown
        formats_arg = self.args.get("formats", "markdown")
        if isinstance(formats_arg, str):
            formats = [f.strip() for f in formats_arg.split(",")]
        else:
            formats = formats_arg
        
        # Optional parameters
        wait_ms = int(self.args.get("wait", 0))
        parser_id = self.args.get("parser", None)
        country = self.args.get("country", None)
        
        self.set_progress(f"Scraping {url}...")
        
        result = await olostep_api.scrape_url(
            url=url,
            formats=formats,
            wait_before_scraping=wait_ms,
            parser_id=parser_id,
            country=country,
        )
        
        # Extract the relevant content from the result
        output_parts = []
        result_data = result.get("result", {})
        
        if result_data.get("markdown_content"):
            output_parts.append(f"## Markdown Content\n\n{result_data['markdown_content']}")
        
        if result_data.get("text_content"):
            output_parts.append(f"## Text Content\n\n{result_data['text_content']}")
        
        if result_data.get("json_content"):
            import json
            json_str = json.dumps(result_data['json_content'], indent=2) if isinstance(result_data['json_content'], (dict, list)) else str(result_data['json_content'])
            output_parts.append(f"## JSON Content\n\n```json\n{json_str}\n```")
        
        if result_data.get("html_content") and "markdown" not in formats:
            # Only include HTML if markdown wasn't requested (to avoid duplication)
            output_parts.append(f"## HTML Content\n\n{result_data['html_content'][:5000]}...")
        
        # Include metadata
        metadata = result_data.get("page_metadata", {})
        if metadata:
            output_parts.append(f"\n## Page Metadata\n- Title: {metadata.get('title', 'N/A')}\n- Status: {metadata.get('status_code', 'N/A')}")
        
        # Include links if available
        links = result_data.get("links_on_page", [])
        if links and len(links) > 0:
            links_preview = links[:20]  # Limit to first 20 links
            links_str = "\n".join([f"- {link}" for link in links_preview])
            if len(links) > 20:
                links_str += f"\n... and {len(links) - 20} more links"
            output_parts.append(f"\n## Links on Page\n{links_str}")
        
        output = "\n\n".join(output_parts) if output_parts else "No content extracted"
        
        return Response(message=output, break_loop=False)
    
    async def _search(self) -> Response:
        """Search the web and get an AI-powered answer."""
        query = self.args.get("query", "") or self.args.get("task", "")
        if not query:
            return Response(
                message="Error: 'query' argument is required for search",
                break_loop=False,
            )
        
        # Optional JSON format for structured responses
        json_format = self.args.get("json_format", None)
        if json_format and isinstance(json_format, str):
            import json
            try:
                json_format = json.loads(json_format)
            except:
                json_format = None
        
        self.set_progress(f"Searching: {query}...")
        
        result = await olostep_api.get_answer(
            task=query,
            json_format=json_format,
        )
        
        # Format the response
        output_parts = []
        result_data = result.get("result", {})
        
        if result_data.get("json_content"):
            import json
            content = result_data['json_content']
            if isinstance(content, str):
                try:
                    content = json.loads(content)
                except:
                    pass
            if isinstance(content, (dict, list)):
                output_parts.append(f"## Answer\n\n```json\n{json.dumps(content, indent=2)}\n```")
            else:
                output_parts.append(f"## Answer\n\n{content}")
        
        # Include sources if available
        sources = result.get("sources", [])
        if sources:
            sources_str = "\n".join([f"- {s}" for s in sources[:10]])
            output_parts.append(f"\n## Sources\n{sources_str}")
        
        output = "\n\n".join(output_parts) if output_parts else "No answer found"
        
        return Response(message=output, break_loop=False)
    
    async def _google_search(self) -> Response:
        """Perform a Google search with structured results."""
        query = self.args.get("query", "")
        if not query:
            return Response(
                message="Error: 'query' argument is required for Google search",
                break_loop=False,
            )
        
        country = self.args.get("country", "us")
        language = self.args.get("language", "en")
        num_results = int(self.args.get("num_results", 10))
        
        self.set_progress(f"Google search: {query}...")
        
        result = await olostep_api.google_search(
            query=query,
            country=country,
            language=language,
            num_results=num_results,
        )
        
        # Format the response
        result_data = result.get("result", {})
        json_content = result_data.get("json_content", {})
        
        if isinstance(json_content, str):
            import json
            try:
                json_content = json.loads(json_content)
            except:
                return Response(message=f"Search results:\n{json_content}", break_loop=False)
        
        output_parts = []
        
        # AI Overview if available
        ai_overview = json_content.get("ai_overview", "")
        if ai_overview:
            output_parts.append(f"## AI Overview\n{ai_overview}")
        
        # Organic results
        organic_results = json_content.get("organic_results", [])
        if organic_results:
            results_str = ""
            for i, r in enumerate(organic_results[:10], 1):
                title = r.get("title", "No title")
                url = r.get("url", "")
                description = r.get("description", "")
                results_str += f"{i}. **{title}**\n   {url}\n   {description}\n\n"
            output_parts.append(f"## Search Results\n{results_str}")
        
        # Related searches
        related = json_content.get("related_searches", [])
        if related:
            related_str = ", ".join(related[:5])
            output_parts.append(f"## Related Searches\n{related_str}")
        
        output = "\n\n".join(output_parts) if output_parts else "No results found"
        
        return Response(message=output, break_loop=False)
    
    async def _map_website(self) -> Response:
        """Map a website to discover all URLs."""
        url = self.args.get("url", "")
        if not url:
            return Response(
                message="Error: 'url' argument is required for mapping",
                break_loop=False,
            )
        
        include_urls = self.args.get("include_urls", None)
        exclude_urls = self.args.get("exclude_urls", None)
        top_n = self.args.get("top_n", None)
        
        if include_urls and isinstance(include_urls, str):
            include_urls = [p.strip() for p in include_urls.split(",")]
        
        if exclude_urls and isinstance(exclude_urls, str):
            exclude_urls = [p.strip() for p in exclude_urls.split(",")]
        
        if top_n:
            top_n = int(top_n)
        
        self.set_progress(f"Mapping website: {url}...")
        
        result = await olostep_api.map_website(
            url=url,
            include_urls=include_urls,
            exclude_urls=exclude_urls,
            top_n=top_n,
        )
        
        urls = result.get("urls", [])
        cursor = result.get("cursor", None)
        
        output_parts = [f"## Website Map: {url}\n"]
        output_parts.append(f"Found {len(urls)} URLs:\n")
        
        # Show first 50 URLs
        for u in urls[:50]:
            output_parts.append(f"- {u}")
        
        if len(urls) > 50:
            output_parts.append(f"\n... and {len(urls) - 50} more URLs")
        
        if cursor:
            output_parts.append(f"\n(More results available, use cursor: {cursor})")
        
        return Response(message="\n".join(output_parts), break_loop=False)
