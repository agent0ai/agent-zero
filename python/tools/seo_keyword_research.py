import asyncio
import aiohttp
import json
from typing import Dict, List, Any
from python.helpers.tool import Tool, Response
from python.helpers.print_style import PrintStyle
from python.helpers.errors import handle_error


class SEOKeywordResearch(Tool):
    """
    Tool for SEO keyword research and analysis.
    Supports multiple data sources and provides keyword suggestions, search volume estimates,
    and competition analysis.
    """

    async def execute(self, **kwargs):
        action = self.args.get("action", "").lower().strip()

        try:
            if action == "suggest_keywords":
                seed_keyword = self.args.get("seed_keyword", "")
                response = await self.suggest_keywords(seed_keyword)
            elif action == "analyze_keyword":
                keyword = self.args.get("keyword", "")
                response = await self.analyze_keyword(keyword)
            elif action == "competitor_keywords":
                competitor_url = self.args.get("competitor_url", "")
                response = await self.competitor_keywords(competitor_url)
            elif action == "keyword_difficulty":
                keyword = self.args.get("keyword", "")
                response = await self.keyword_difficulty(keyword)
            elif action == "related_questions":
                keyword = self.args.get("keyword", "")
                response = await self.related_questions(keyword)
            elif action == "local_keyword_suggestions":
                keyword = self.args.get("keyword", "")
                location = self.args.get("location", "")
                response = await self.local_keyword_suggestions(keyword, location)
            else:
                response = f"""Unknown action: {action}

Available actions:
- suggest_keywords: Generate keyword suggestions from seed keyword
- analyze_keyword: Analyze specific keyword metrics
- competitor_keywords: Find keywords competitors rank for
- keyword_difficulty: Assess ranking difficulty for keyword
- related_questions: Find "People Also Ask" questions
- local_keyword_suggestions: Get location-based keyword variations

Note: This tool provides basic keyword research. For advanced features, integrate with:
- SEMrush API (commercial)
- Ahrefs API (commercial)
- Google Keyword Planner API (free, requires Google Ads account)
- DataForSEO API (commercial)

Store API keys using memory_save tool with keys like: semrush_api_key, ahrefs_api_key"""

            return Response(message=response, break_loop=False)

        except Exception as e:
            error_msg = f"SEO Keyword Research Error: {str(e)}"
            handle_error(e)
            return Response(message=error_msg, break_loop=False)

    async def suggest_keywords(self, seed_keyword: str) -> str:
        """Generate keyword suggestions using Google Autocomplete API"""
        if not seed_keyword:
            return "Error: seed_keyword is required"

        try:
            # Use Google Autocomplete API (public, no key required)
            suggestions = await self._get_google_suggestions(seed_keyword)

            # Generate variations
            variations = self._generate_keyword_variations(seed_keyword)

            result = {
                "seed_keyword": seed_keyword,
                "autocomplete_suggestions": suggestions,
                "keyword_variations": variations,
                "total_suggestions": len(suggestions) + len(variations)
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            return f"Failed to suggest keywords: {str(e)}"

    async def _get_google_suggestions(self, keyword: str) -> List[str]:
        """Fetch Google autocomplete suggestions"""
        url = "http://suggestqueries.google.com/complete/search"
        params = {
            "client": "firefox",
            "q": keyword
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data[1] if len(data) > 1 else []
                    return []
        except Exception as e:
            PrintStyle.error(f"Failed to fetch Google suggestions: {str(e)}")
            return []

    def _generate_keyword_variations(self, seed_keyword: str) -> List[str]:
        """Generate keyword variations using common patterns"""
        variations = []

        # Question words
        question_words = ["how", "what", "why", "when", "where", "who", "which"]
        for word in question_words:
            variations.append(f"{word} {seed_keyword}")
            variations.append(f"{word} to {seed_keyword}")

        # Modifiers
        modifiers = [
            "best", "top", "guide", "tutorial", "tips", "free", "online",
            "cheap", "affordable", "professional", "vs", "review", "comparison"
        ]
        for mod in modifiers:
            variations.append(f"{mod} {seed_keyword}")
            variations.append(f"{seed_keyword} {mod}")

        # Time-based
        time_words = ["2024", "2025", "now", "today"]
        for time in time_words:
            variations.append(f"{seed_keyword} {time}")

        return variations[:30]  # Limit to 30 variations

    async def analyze_keyword(self, keyword: str) -> str:
        """Analyze a specific keyword"""
        if not keyword:
            return "Error: keyword is required"

        try:
            # Basic analysis without external APIs
            analysis = {
                "keyword": keyword,
                "word_count": len(keyword.split()),
                "character_length": len(keyword),
                "type": self._classify_keyword_type(keyword),
                "suggestions": await self._get_google_suggestions(keyword),
                "optimization_tips": self._get_optimization_tips(keyword)
            }

            # If API keys are available, fetch advanced metrics
            semrush_key = self.agent.get_data("semrush_api_key")
            if semrush_key:
                analysis["semrush_data"] = "API integration available - implement semrush_api_call"

            return json.dumps(analysis, indent=2)

        except Exception as e:
            return f"Failed to analyze keyword: {str(e)}"

    def _classify_keyword_type(self, keyword: str) -> str:
        """Classify keyword by intent and length"""
        word_count = len(keyword.split())

        if word_count == 1:
            length_type = "Short-tail (high competition, broad intent)"
        elif word_count == 2:
            length_type = "Medium-tail (moderate competition, specific intent)"
        else:
            length_type = "Long-tail (low competition, specific intent)"

        # Check intent
        question_words = ["how", "what", "why", "when", "where", "who"]
        commercial_words = ["buy", "price", "cheap", "best", "review", "vs", "comparison"]
        transactional_words = ["buy", "purchase", "order", "download", "get"]

        keyword_lower = keyword.lower()

        if any(word in keyword_lower for word in question_words):
            intent = "Informational"
        elif any(word in keyword_lower for word in transactional_words):
            intent = "Transactional"
        elif any(word in keyword_lower for word in commercial_words):
            intent = "Commercial Investigation"
        else:
            intent = "Navigational/Informational"

        return f"{length_type} | Intent: {intent}"

    def _get_optimization_tips(self, keyword: str) -> List[str]:
        """Provide keyword optimization tips"""
        tips = []
        word_count = len(keyword.split())

        if word_count == 1:
            tips.append("Short-tail keyword: Very competitive, consider long-tail variations")
            tips.append("Use this keyword in H1, title tag, and meta description")
        else:
            tips.append("Good keyword length for targeting specific queries")

        if len(keyword) > 60:
            tips.append("Keyword is very long, may not match exact user queries")

        if keyword.lower().startswith(("how", "what", "why")):
            tips.append("Question-based keyword: Create FAQ content, featured snippet opportunities")

        if any(word in keyword.lower() for word in ["best", "top", "review"]):
            tips.append("Commercial intent: Create comparison/review content with CTAs")

        tips.append("Include keyword naturally in first paragraph")
        tips.append("Use semantic variations and related terms throughout content")

        return tips

    async def related_questions(self, keyword: str) -> str:
        """Find related questions (People Also Ask simulation)"""
        if not keyword:
            return "Error: keyword is required"

        # Generate common question patterns
        questions = []

        question_templates = [
            f"What is {keyword}?",
            f"How does {keyword} work?",
            f"Why is {keyword} important?",
            f"When should I use {keyword}?",
            f"Where can I find {keyword}?",
            f"How to {keyword}?",
            f"What are the benefits of {keyword}?",
            f"How much does {keyword} cost?",
            f"Is {keyword} worth it?",
            f"What are the best {keyword}?"
        ]

        result = {
            "keyword": keyword,
            "related_questions": question_templates,
            "content_strategy": [
                "Create comprehensive FAQ section answering these questions",
                "Use questions as H2/H3 headings in content",
                "Optimize for featured snippets with concise answers",
                "Create individual blog posts for high-value questions"
            ]
        }

        return json.dumps(result, indent=2)

    async def local_keyword_suggestions(self, keyword: str, location: str) -> str:
        """Generate local SEO keyword variations"""
        if not keyword or not location:
            return "Error: Both keyword and location are required"

        local_variations = [
            f"{keyword} in {location}",
            f"{keyword} near {location}",
            f"{keyword} {location}",
            f"{location} {keyword}",
            f"best {keyword} in {location}",
            f"{keyword} near me",
            f"local {keyword} {location}",
            f"top {keyword} {location}",
            f"affordable {keyword} {location}",
            f"{keyword} services {location}"
        ]

        result = {
            "base_keyword": keyword,
            "location": location,
            "local_variations": local_variations,
            "local_seo_tips": [
                "Create Google Business Profile and optimize with these keywords",
                "Include location in title tags and H1",
                "Add location-specific content and landing pages",
                "Get local citations and backlinks",
                "Encourage customer reviews mentioning location"
            ]
        }

        return json.dumps(result, indent=2)

    async def competitor_keywords(self, competitor_url: str) -> str:
        """Analyze competitor keywords (requires external API or scraping)"""
        if not competitor_url:
            return "Error: competitor_url is required"

        # This would require API integration with SEMrush, Ahrefs, etc.
        return json.dumps({
            "competitor_url": competitor_url,
            "status": "API integration required",
            "recommendation": "To analyze competitor keywords, integrate with:\n"
                             "- SEMrush API: Get semrush_api_key and implement API calls\n"
                             "- Ahrefs API: Get ahrefs_api_key and implement API calls\n"
                             "- Manual method: Use code_execution_tool to scrape and analyze competitor site content"
        }, indent=2)

    async def keyword_difficulty(self, keyword: str) -> str:
        """Assess keyword difficulty (basic analysis)"""
        if not keyword:
            return "Error: keyword is required"

        # Basic difficulty assessment
        word_count = len(keyword.split())
        keyword_lower = keyword.lower()

        difficulty_score = 50  # Base score

        # Adjust based on keyword length
        if word_count == 1:
            difficulty_score += 30
        elif word_count >= 4:
            difficulty_score -= 20

        # Adjust based on commercial intent
        commercial_words = ["buy", "price", "cheap", "best", "vs"]
        if any(word in keyword_lower for word in commercial_words):
            difficulty_score += 15

        difficulty_score = max(0, min(100, difficulty_score))

        if difficulty_score < 30:
            difficulty_level = "Easy (good opportunity)"
        elif difficulty_score < 60:
            difficulty_level = "Medium (achievable with effort)"
        else:
            difficulty_level = "Hard (requires significant authority)"

        result = {
            "keyword": keyword,
            "estimated_difficulty_score": difficulty_score,
            "difficulty_level": difficulty_level,
            "ranking_factors": [
                "Domain authority and age",
                "Quality backlink profile",
                "Content quality and depth",
                "User engagement signals",
                "Technical SEO optimization"
            ],
            "recommendation": "For accurate difficulty scores, integrate with SEMrush or Ahrefs API"
        }

        return json.dumps(result, indent=2)
