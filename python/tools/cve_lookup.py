import asyncio
import json
import re
import urllib.parse
from python.helpers.tool import Tool, Response
from python.helpers.errors import handle_error


NVD_API_BASE = "https://services.nvd.nist.gov/rest/json/cves/2.0"
EXPLOITDB_BASE = "https://www.exploit-db.com/search"


class CVELookup(Tool):
    """
    Look up CVE details and known public exploits.

    Actions:
        lookup_cve     — fetch details for a specific CVE ID (e.g. CVE-2021-44228)
        search_product — search CVEs by product name and optional version
    """

    async def execute(self, action="lookup_cve", cve_id="", product="", version="", **kwargs):
        action = action.lower().strip()

        if action == "lookup_cve":
            if not cve_id:
                return Response(message="lookup_cve requires 'cve_id' (e.g. CVE-2021-44228).", break_loop=False)
            return await self._lookup_cve(cve_id.strip().upper())

        if action == "search_product":
            if not product:
                return Response(message="search_product requires 'product' argument.", break_loop=False)
            return await self._search_product(product.strip(), version.strip())

        return Response(
            message=f"Unknown action '{action}'. Valid: lookup_cve, search_product",
            break_loop=False,
        )

    async def _lookup_cve(self, cve_id: str) -> Response:
        try:
            import aiohttp  # type: ignore

            url = f"{NVD_API_BASE}?cveId={urllib.parse.quote(cve_id)}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status != 200:
                        raise ValueError(f"NVD API returned HTTP {resp.status}")
                    data = await resp.json()

            vulns = data.get("vulnerabilities", [])
            if not vulns:
                return Response(message=f"No NVD entry found for {cve_id}.", break_loop=False)

            cve = vulns[0]["cve"]
            return Response(message=self._format_cve(cve), break_loop=False)

        except ImportError:
            return await self._fallback_search(cve_id)
        except Exception as e:
            handle_error(e)
            return await self._fallback_search(cve_id)

    async def _search_product(self, product: str, version: str) -> Response:
        try:
            import aiohttp  # type: ignore

            keyword = f"{product} {version}".strip()
            url = f"{NVD_API_BASE}?keywordSearch={urllib.parse.quote(keyword)}&resultsPerPage=10"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status != 200:
                        raise ValueError(f"NVD API returned HTTP {resp.status}")
                    data = await resp.json()

            vulns = data.get("vulnerabilities", [])
            if not vulns:
                return Response(message=f"No CVEs found for '{keyword}'.", break_loop=False)

            lines = [f"CVEs found for '{keyword}': {data.get('totalResults', len(vulns))} total (showing {len(vulns)})\n"]
            for v in vulns:
                cve = v["cve"]
                cve_id = cve.get("id", "?")
                desc = (cve.get("descriptions", [{}])[0].get("value", "No description")[:120] + "...")
                score = self._extract_cvss_score(cve)
                lines.append(f"  {cve_id}  CVSS: {score}  {desc}")

            return Response(message="\n".join(lines), break_loop=False)

        except ImportError:
            return await self._fallback_search(f"{product} {version} CVE exploit")
        except Exception as e:
            handle_error(e)
            return await self._fallback_search(f"{product} {version} CVE exploit")

    def _format_cve(self, cve: dict) -> str:
        cve_id = cve.get("id", "?")
        descriptions = cve.get("descriptions", [])
        desc = next((d["value"] for d in descriptions if d.get("lang") == "en"), "No description")

        score_str = self._extract_cvss_score(cve)
        vector_str = self._extract_cvss_vector(cve)

        refs = cve.get("references", [])
        ref_lines = []
        for r in refs[:5]:
            tags = ", ".join(r.get("tags", []))
            ref_lines.append(f"  - {r.get('url', '')}  [{tags}]")

        weaknesses = cve.get("weaknesses", [])
        cwes = []
        for w in weaknesses:
            for d in w.get("description", []):
                cwes.append(d.get("value", ""))

        lines = [
            f"## {cve_id}",
            f"**CVSS Score:** {score_str}",
        ]
        if vector_str:
            lines.append(f"**CVSS Vector:** {vector_str}")
        if cwes:
            lines.append(f"**CWE:** {', '.join(cwes)}")
        lines.append(f"\n**Description:**\n{desc}")
        if ref_lines:
            lines.append(f"\n**References:**\n" + "\n".join(ref_lines))
        lines.append(
            f"\n**Next steps:** Search for PoC with:\n"
            f"  searchsploit {cve_id}\n"
            f"  msfconsole -q -x 'search {cve_id}'\n"
            f"  GitHub: https://github.com/search?q={cve_id}&type=repositories"
        )

        return "\n".join(lines)

    def _extract_cvss_score(self, cve: dict) -> str:
        metrics = cve.get("metrics", {})
        for key in ["cvssMetricV31", "cvssMetricV30", "cvssMetricV2"]:
            entries = metrics.get(key, [])
            if entries:
                data = entries[0].get("cvssData", {})
                score = data.get("baseScore", "?")
                severity = data.get("baseSeverity", "")
                return f"{score} ({severity})" if severity else str(score)
        return "N/A"

    def _extract_cvss_vector(self, cve: dict) -> str:
        metrics = cve.get("metrics", {})
        for key in ["cvssMetricV31", "cvssMetricV30", "cvssMetricV2"]:
            entries = metrics.get(key, [])
            if entries:
                return entries[0].get("cvssData", {}).get("vectorString", "")
        return ""

    async def _fallback_search(self, query: str) -> Response:
        """Fall back to the agent's search engine if NVD API is unavailable."""
        from python.helpers.searxng import search as searxng

        try:
            results = await searxng(f"{query} exploit site:exploit-db.com OR site:github.com OR site:nvd.nist.gov")
            if isinstance(results, Exception):
                return Response(
                    message=f"NVD API and search fallback both failed. Try: searchsploit {query}",
                    break_loop=False,
                )
            items = results.get("results", [])[:5]
            lines = [f"NVD API unavailable. Web search results for '{query}':\n"]
            for item in items:
                lines.append(f"  {item.get('title', '')}  {item.get('url', '')}")
                if item.get("content"):
                    lines.append(f"    {item['content'][:120]}")
            return Response(message="\n".join(lines), break_loop=False)
        except Exception as e:
            handle_error(e)
            return Response(
                message=f"CVE lookup failed. Run manually: searchsploit {query}",
                break_loop=False,
            )
