import asyncio
import aiohttp
import json
import re
from typing import Dict, List, Any
from urllib.parse import urlparse, urljoin
from python.helpers.tool import Tool, Response
from python.helpers.print_style import PrintStyle
from python.helpers.errors import handle_error


class SEOTechnicalAudit(Tool):
    """
    Tool for performing technical SEO audits on websites.
    Checks site speed, mobile-friendliness, schema markup, robots.txt, sitemap, and more.
    """

    async def execute(self, **kwargs):
        action = self.args.get("action", "").lower().strip()
        site_url = self.args.get("site_url", "").strip()

        if not site_url and action not in ["help"]:
            return Response(message="Error: site_url is required", break_loop=False)

        if not site_url.startswith(("http://", "https://")):
            site_url = "https://" + site_url

        try:
            if action == "full_audit":
                response = await self.full_audit(site_url)
            elif action == "check_robots":
                response = await self.check_robots(site_url)
            elif action == "check_sitemap":
                response = await self.check_sitemap(site_url)
            elif action == "check_ssl":
                response = await self.check_ssl(site_url)
            elif action == "check_meta_tags":
                response = await self.check_meta_tags(site_url)
            elif action == "check_schema":
                response = await self.check_schema(site_url)
            elif action == "check_mobile":
                response = await self.check_mobile(site_url)
            elif action == "check_page_speed":
                response = await self.check_page_speed(site_url)
            else:
                response = f"""Unknown action: {action}

Available actions:
- full_audit: Complete technical SEO audit
- check_robots: Check robots.txt file
- check_sitemap: Verify XML sitemap
- check_ssl: Verify HTTPS/SSL certificate
- check_meta_tags: Analyze meta tags
- check_schema: Check structured data/schema markup
- check_mobile: Mobile-friendliness check
- check_page_speed: Page speed analysis"""

            return Response(message=response, break_loop=False)

        except Exception as e:
            error_msg = f"SEO Technical Audit Error: {str(e)}"
            handle_error(e)
            return Response(message=error_msg, break_loop=False)

    async def full_audit(self, site_url: str) -> str:
        """Perform comprehensive technical SEO audit"""
        PrintStyle.info(f"Starting full technical SEO audit for {site_url}")

        results = {
            "site_url": site_url,
            "audit_results": {}
        }

        # Run all checks
        checks = [
            ("SSL/HTTPS", self.check_ssl(site_url)),
            ("Robots.txt", self.check_robots(site_url)),
            ("Sitemap", self.check_sitemap(site_url)),
            ("Meta Tags", self.check_meta_tags(site_url)),
            ("Schema Markup", self.check_schema(site_url)),
            ("Mobile", self.check_mobile(site_url)),
        ]

        for check_name, check_coro in checks:
            try:
                result = await check_coro
                results["audit_results"][check_name] = json.loads(result) if isinstance(result, str) else result
            except Exception as e:
                results["audit_results"][check_name] = {"error": str(e)}

        # Calculate overall score
        results["overall_score"] = self._calculate_audit_score(results["audit_results"])

        return json.dumps(results, indent=2)

    async def check_robots(self, site_url: str) -> str:
        """Check robots.txt file"""
        robots_url = urljoin(site_url, "/robots.txt")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(robots_url, timeout=10) as resp:
                    if resp.status == 200:
                        content = await resp.text()

                        analysis = {
                            "url": robots_url,
                            "status": "Found",
                            "content_length": len(content),
                            "has_sitemap": "sitemap:" in content.lower(),
                            "has_disallow": "disallow:" in content.lower(),
                            "user_agents": len(re.findall(r'user-agent:', content, re.IGNORECASE)),
                            "issues": []
                        }

                        if not analysis["has_sitemap"]:
                            analysis["issues"].append("No sitemap reference found in robots.txt")

                        if "disallow: /" in content.lower() and "allow:" not in content.lower():
                            analysis["issues"].append("Warning: Site may be blocking all crawlers")

                        if not analysis["issues"]:
                            analysis["issues"].append("No issues found")

                        return json.dumps(analysis, indent=2)
                    else:
                        return json.dumps({
                            "url": robots_url,
                            "status": "Not Found",
                            "recommendation": "Create robots.txt file to guide search engine crawlers"
                        }, indent=2)

        except Exception as e:
            return json.dumps({"error": f"Failed to check robots.txt: {str(e)}"}, indent=2)

    async def check_sitemap(self, site_url: str) -> str:
        """Check for XML sitemap"""
        sitemap_urls = [
            urljoin(site_url, "/sitemap.xml"),
            urljoin(site_url, "/sitemap_index.xml"),
            urljoin(site_url, "/wp-sitemap.xml"),  # WordPress default
        ]

        async with aiohttp.ClientSession() as session:
            for sitemap_url in sitemap_urls:
                try:
                    async with session.get(sitemap_url, timeout=10) as resp:
                        if resp.status == 200:
                            content = await resp.text()

                            url_count = len(re.findall(r'<url>', content))
                            sitemap_count = len(re.findall(r'<sitemap>', content))

                            return json.dumps({
                                "url": sitemap_url,
                                "status": "Found",
                                "type": "Sitemap Index" if sitemap_count > 0 else "Regular Sitemap",
                                "url_count": url_count,
                                "sitemap_count": sitemap_count,
                                "has_lastmod": "<lastmod>" in content,
                                "recommendation": "Sitemap found and accessible"
                            }, indent=2)
                except:
                    continue

        return json.dumps({
            "status": "Not Found",
            "checked_urls": sitemap_urls,
            "recommendation": "Create XML sitemap and submit to Google Search Console"
        }, indent=2)

    async def check_ssl(self, site_url: str) -> str:
        """Check SSL/HTTPS configuration"""
        parsed = urlparse(site_url)

        result = {
            "protocol": parsed.scheme,
            "has_https": parsed.scheme == "https",
            "issues": []
        }

        if not result["has_https"]:
            result["issues"].append("Site not using HTTPS - critical SEO issue")
            result["recommendation"] = "Install SSL certificate and redirect HTTP to HTTPS"
        else:
            result["issues"].append("No issues - HTTPS properly configured")
            result["recommendation"] = "Ensure all resources load over HTTPS"

        return json.dumps(result, indent=2)

    async def check_meta_tags(self, site_url: str) -> str:
        """Check meta tags on homepage"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(site_url, timeout=15) as resp:
                    html = await resp.text()

            # Extract meta tags
            title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
            title = title_match.group(1).strip() if title_match else None

            desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)["\']', html, re.IGNORECASE)
            description = desc_match.group(1) if desc_match else None

            viewport_match = re.search(r'<meta[^>]*name=["\']viewport["\']', html, re.IGNORECASE)
            has_viewport = bool(viewport_match)

            canonical_match = re.search(r'<link[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']*)["\']', html, re.IGNORECASE)
            canonical = canonical_match.group(1) if canonical_match else None

            # Open Graph tags
            og_title = re.search(r'<meta[^>]*property=["\']og:title["\'][^>]*content=["\']([^"\']*)["\']', html, re.IGNORECASE)
            og_desc = re.search(r'<meta[^>]*property=["\']og:description["\'][^>]*content=["\']([^"\']*)["\']', html, re.IGNORECASE)

            analysis = {
                "title": {
                    "content": title,
                    "length": len(title) if title else 0,
                    "status": "Good" if title and 30 <= len(title) <= 60 else "Needs optimization"
                },
                "meta_description": {
                    "content": description,
                    "length": len(description) if description else 0,
                    "status": "Good" if description and 120 <= len(description) <= 160 else "Needs optimization"
                },
                "viewport": has_viewport,
                "canonical": canonical,
                "open_graph": {
                    "has_og_title": bool(og_title),
                    "has_og_description": bool(og_desc)
                },
                "recommendations": []
            }

            if not title:
                analysis["recommendations"].append("Add title tag (critical)")
            elif len(title) > 60:
                analysis["recommendations"].append("Title too long (keep under 60 characters)")
            elif len(title) < 30:
                analysis["recommendations"].append("Title too short (aim for 30-60 characters)")

            if not description:
                analysis["recommendations"].append("Add meta description (important)")
            elif len(description) > 160:
                analysis["recommendations"].append("Meta description too long (keep under 160 characters)")

            if not has_viewport:
                analysis["recommendations"].append("Add viewport meta tag for mobile responsiveness")

            if not canonical:
                analysis["recommendations"].append("Add canonical URL to prevent duplicate content issues")

            if not analysis["recommendations"]:
                analysis["recommendations"].append("Meta tags are well optimized")

            return json.dumps(analysis, indent=2)

        except Exception as e:
            return json.dumps({"error": f"Failed to check meta tags: {str(e)}"}, indent=2)

    async def check_schema(self, site_url: str) -> str:
        """Check for structured data/schema markup"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(site_url, timeout=15) as resp:
                    html = await resp.text()

            # Look for JSON-LD schema
            jsonld_matches = re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
                                       html, re.IGNORECASE | re.DOTALL)

            # Look for microdata
            has_microdata = bool(re.search(r'itemscope|itemprop', html, re.IGNORECASE))

            # Look for RDFa
            has_rdfa = bool(re.search(r'vocab=|property=', html, re.IGNORECASE))

            schema_types = []
            if jsonld_matches:
                for match in jsonld_matches:
                    try:
                        data = json.loads(match.strip())
                        if isinstance(data, dict) and "@type" in data:
                            schema_types.append(data["@type"])
                        elif isinstance(data, list):
                            for item in data:
                                if isinstance(item, dict) and "@type" in item:
                                    schema_types.append(item["@type"])
                    except:
                        pass

            result = {
                "has_schema": len(jsonld_matches) > 0 or has_microdata or has_rdfa,
                "jsonld_count": len(jsonld_matches),
                "has_microdata": has_microdata,
                "has_rdfa": has_rdfa,
                "schema_types": list(set(schema_types)),
                "recommendations": []
            }

            if not result["has_schema"]:
                result["recommendations"].append("Add structured data markup (JSON-LD recommended)")
                result["recommendations"].append("Common types: Organization, WebSite, Article, BreadcrumbList")
            else:
                result["recommendations"].append("Schema markup detected - validate with Google Rich Results Test")

            return json.dumps(result, indent=2)

        except Exception as e:
            return json.dumps({"error": f"Failed to check schema: {str(e)}"}, indent=2)

    async def check_mobile(self, site_url: str) -> str:
        """Check mobile-friendliness"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(site_url, timeout=15) as resp:
                    html = await resp.text()

            viewport_match = re.search(r'<meta[^>]*name=["\']viewport["\'][^>]*content=["\']([^"\']*)["\']',
                                      html, re.IGNORECASE)
            viewport = viewport_match.group(1) if viewport_match else None

            has_responsive_viewport = viewport and "width=device-width" in viewport.lower()

            result = {
                "has_viewport_meta": bool(viewport),
                "viewport_content": viewport,
                "is_responsive": has_responsive_viewport,
                "recommendations": []
            }

            if not has_responsive_viewport:
                result["recommendations"].append("Add viewport meta tag: <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">")
            else:
                result["recommendations"].append("Viewport meta tag configured correctly")
                result["recommendations"].append("Test with Google Mobile-Friendly Test for full analysis")

            return json.dumps(result, indent=2)

        except Exception as e:
            return json.dumps({"error": f"Failed to check mobile: {str(e)}"}, indent=2)

    async def check_page_speed(self, site_url: str) -> str:
        """Basic page speed check"""
        try:
            import time
            start_time = time.time()

            async with aiohttp.ClientSession() as session:
                async with session.get(site_url, timeout=30) as resp:
                    html = await resp.text()
                    load_time = time.time() - start_time

            html_size = len(html.encode('utf-8'))

            result = {
                "load_time_seconds": round(load_time, 2),
                "html_size_kb": round(html_size / 1024, 2),
                "status": "Good" if load_time < 3 else "Needs improvement",
                "recommendations": []
            }

            if load_time > 5:
                result["recommendations"].append("Page load time too slow (>5s) - optimize immediately")
            elif load_time > 3:
                result["recommendations"].append("Page load time could be improved (aim for <3s)")
            else:
                result["recommendations"].append("Page load time is good")

            result["recommendations"].append("Use Google PageSpeed Insights for detailed analysis")
            result["recommendations"].append("Consider: image optimization, caching, minification, CDN")

            return json.dumps(result, indent=2)

        except Exception as e:
            return json.dumps({"error": f"Failed to check page speed: {str(e)}"}, indent=2)

    def _calculate_audit_score(self, audit_results: Dict) -> Dict:
        """Calculate overall audit score"""
        score = 0
        max_score = 100

        checks = {
            "SSL/HTTPS": 20,
            "Robots.txt": 10,
            "Sitemap": 15,
            "Meta Tags": 25,
            "Schema Markup": 15,
            "Mobile": 15
        }

        for check_name, points in checks.items():
            if check_name in audit_results:
                result = audit_results[check_name]
                if isinstance(result, dict) and "error" not in result:
                    # Scoring logic based on check results
                    if check_name == "SSL/HTTPS" and result.get("has_https"):
                        score += points
                    elif check_name == "Robots.txt" and result.get("status") == "Found":
                        score += points
                    elif check_name == "Sitemap" and result.get("status") == "Found":
                        score += points
                    elif check_name == "Meta Tags":
                        if result.get("title", {}).get("status") == "Good":
                            score += points * 0.5
                        if result.get("meta_description", {}).get("status") == "Good":
                            score += points * 0.5
                    elif check_name == "Schema Markup" and result.get("has_schema"):
                        score += points
                    elif check_name == "Mobile" and result.get("is_responsive"):
                        score += points

        if score >= 80:
            rating = "Excellent"
        elif score >= 60:
            rating = "Good"
        elif score >= 40:
            rating = "Fair"
        else:
            rating = "Poor"

        return {
            "score": round(score),
            "max_score": max_score,
            "percentage": f"{round(score)}%",
            "rating": rating
        }
