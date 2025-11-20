import re
import json
from typing import Dict, List, Any, Tuple
from html.parser import HTMLParser
from python.helpers.tool import Tool, Response
from python.helpers.print_style import PrintStyle
from python.helpers.errors import handle_error


class HTMLTextExtractor(HTMLParser):
    """Extract text content from HTML"""
    def __init__(self):
        super().__init__()
        self.text = []
        self.headings = {"h1": [], "h2": [], "h3": [], "h4": [], "h5": [], "h6": []}
        self.current_heading = None

    def handle_starttag(self, tag, attrs):
        if tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            self.current_heading = tag

    def handle_endtag(self, tag):
        if tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            self.current_heading = None

    def handle_data(self, data):
        text = data.strip()
        if text:
            self.text.append(text)
            if self.current_heading:
                self.headings[self.current_heading].append(text)

    def get_text(self):
        return " ".join(self.text)


class SEOContentAnalyzer(Tool):
    """
    Tool for analyzing content for SEO optimization.
    Checks keyword usage, content structure, readability, and provides actionable recommendations.
    """

    async def execute(self, **kwargs):
        action = self.args.get("action", "").lower().strip()

        try:
            if action == "analyze_content":
                content = self.args.get("content", "")
                target_keyword = self.args.get("target_keyword", "")
                response = await self.analyze_content(content, target_keyword)
            elif action == "check_keyword_density":
                content = self.args.get("content", "")
                keywords = self.args.get("keywords", [])
                response = await self.check_keyword_density(content, keywords)
            elif action == "analyze_headings":
                content = self.args.get("content", "")
                response = await self.analyze_headings(content)
            elif action == "check_readability":
                content = self.args.get("content", "")
                response = await self.check_readability(content)
            elif action == "find_missing_elements":
                content = self.args.get("content", "")
                response = await self.find_missing_elements(content)
            else:
                response = f"""Unknown action: {action}

Available actions:
- analyze_content: Comprehensive SEO content analysis
- check_keyword_density: Analyze keyword usage and density
- analyze_headings: Check heading structure and hierarchy
- check_readability: Assess content readability
- find_missing_elements: Identify missing SEO elements"""

            return Response(message=response, break_loop=False)

        except Exception as e:
            error_msg = f"SEO Content Analyzer Error: {str(e)}"
            handle_error(e)
            return Response(message=error_msg, break_loop=False)

    async def analyze_content(self, content: str, target_keyword: str) -> str:
        """Comprehensive content SEO analysis"""
        if not content:
            return "Error: content is required"

        # Extract text from HTML if needed
        parser = HTMLTextExtractor()
        try:
            parser.feed(content)
            text_content = parser.get_text()
            headings = parser.headings
        except:
            # If not HTML, use as plain text
            text_content = content
            headings = {"h1": [], "h2": [], "h3": [], "h4": [], "h5": [], "h6": []}

        # Basic metrics
        word_count = len(text_content.split())
        char_count = len(text_content)
        sentence_count = len(re.findall(r'[.!?]+', text_content))

        # Keyword analysis
        keyword_stats = {}
        if target_keyword:
            keyword_stats = self._analyze_keyword_usage(text_content, target_keyword, headings)

        # Heading analysis
        heading_analysis = self._analyze_heading_structure(headings, target_keyword)

        # Readability
        readability = self._calculate_readability(text_content, word_count, sentence_count)

        # SEO score
        seo_score = self._calculate_seo_score(
            word_count, keyword_stats, heading_analysis, text_content
        )

        # Recommendations
        recommendations = self._generate_recommendations(
            word_count, keyword_stats, heading_analysis, readability, text_content
        )

        result = {
            "content_metrics": {
                "word_count": word_count,
                "character_count": char_count,
                "sentence_count": sentence_count,
                "average_sentence_length": round(word_count / sentence_count, 1) if sentence_count > 0 else 0
            },
            "keyword_analysis": keyword_stats,
            "heading_structure": heading_analysis,
            "readability": readability,
            "seo_score": seo_score,
            "recommendations": recommendations
        }

        return json.dumps(result, indent=2)

    def _analyze_keyword_usage(self, text: str, keyword: str, headings: Dict) -> Dict:
        """Analyze how keyword is used in content"""
        text_lower = text.lower()
        keyword_lower = keyword.lower()

        # Count occurrences
        total_occurrences = text_lower.count(keyword_lower)
        word_count = len(text.split())
        density = round((total_occurrences / word_count) * 100, 2) if word_count > 0 else 0

        # Check keyword in first paragraph (first 100 words)
        first_100_words = " ".join(text.split()[:100]).lower()
        in_first_paragraph = keyword_lower in first_100_words

        # Check keyword in headings
        in_h1 = any(keyword_lower in h.lower() for h in headings.get("h1", []))
        in_h2 = any(keyword_lower in h.lower() for h in headings.get("h2", []))
        in_headings = in_h1 or in_h2

        return {
            "target_keyword": keyword,
            "total_occurrences": total_occurrences,
            "keyword_density": f"{density}%",
            "density_status": self._get_density_status(density),
            "in_first_paragraph": in_first_paragraph,
            "in_h1": in_h1,
            "in_h2": in_h2,
            "in_any_heading": in_headings
        }

    def _get_density_status(self, density: float) -> str:
        """Evaluate keyword density"""
        if density < 0.5:
            return "Too low - increase keyword usage naturally"
        elif density <= 2.5:
            return "Optimal - good keyword density"
        else:
            return "Too high - risk of keyword stuffing"

    def _analyze_heading_structure(self, headings: Dict, target_keyword: str = "") -> Dict:
        """Analyze heading hierarchy and structure"""
        h1_count = len(headings.get("h1", []))
        h2_count = len(headings.get("h2", []))
        h3_count = len(headings.get("h3", []))

        issues = []
        if h1_count == 0:
            issues.append("Missing H1 heading (critical)")
        elif h1_count > 1:
            issues.append("Multiple H1 headings (should have only one)")

        if h2_count == 0:
            issues.append("No H2 headings (add subheadings for better structure)")

        if h3_count > h2_count * 3:
            issues.append("Too many H3 relative to H2 (check hierarchy)")

        return {
            "h1_count": h1_count,
            "h2_count": h2_count,
            "h3_count": h3_count,
            "h1_headings": headings.get("h1", []),
            "h2_headings": headings.get("h2", []),
            "issues": issues if issues else ["No structural issues found"],
            "hierarchy_score": "Good" if not issues else "Needs improvement"
        }

    def _calculate_readability(self, text: str, word_count: int, sentence_count: int) -> Dict:
        """Calculate readability metrics (simplified Flesch reading ease)"""
        if word_count == 0 or sentence_count == 0:
            return {"score": 0, "level": "N/A", "status": "Insufficient content"}

        avg_sentence_length = word_count / sentence_count

        # Count syllables (approximate by counting vowel groups)
        syllables = len(re.findall(r'[aeiouy]+', text.lower()))
        avg_syllables_per_word = syllables / word_count if word_count > 0 else 0

        # Simplified Flesch Reading Ease score
        flesch_score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
        flesch_score = max(0, min(100, flesch_score))

        if flesch_score >= 60:
            level = "Easy to read (good for web)"
        elif flesch_score >= 50:
            level = "Fairly easy to read"
        elif flesch_score >= 30:
            level = "Difficult to read"
        else:
            level = "Very difficult to read"

        return {
            "flesch_reading_ease": round(flesch_score, 1),
            "level": level,
            "avg_sentence_length": round(avg_sentence_length, 1),
            "avg_syllables_per_word": round(avg_syllables_per_word, 2),
            "status": "Good" if flesch_score >= 50 else "Needs improvement"
        }

    def _calculate_seo_score(self, word_count: int, keyword_stats: Dict,
                            heading_analysis: Dict, text: str) -> Dict:
        """Calculate overall SEO score out of 100"""
        score = 0
        max_score = 100

        # Word count (20 points)
        if 300 <= word_count <= 3000:
            score += 20
        elif 150 <= word_count < 300 or 3000 < word_count <= 5000:
            score += 10

        # Keyword usage (30 points)
        if keyword_stats:
            if keyword_stats.get("in_h1"):
                score += 10
            if keyword_stats.get("in_first_paragraph"):
                score += 10
            if "Optimal" in keyword_stats.get("density_status", ""):
                score += 10

        # Heading structure (20 points)
        if heading_analysis.get("h1_count") == 1:
            score += 10
        if heading_analysis.get("h2_count") >= 2:
            score += 10

        # Content quality (30 points)
        # Has links (internal/external)
        if re.search(r'<a\s+href=', text):
            score += 10

        # Has images
        if re.search(r'<img\s+', text):
            score += 10

        # Sufficient length
        if word_count >= 600:
            score += 10

        if score >= 80:
            rating = "Excellent"
        elif score >= 60:
            rating = "Good"
        elif score >= 40:
            rating = "Fair"
        else:
            rating = "Needs Improvement"

        return {
            "score": score,
            "max_score": max_score,
            "percentage": f"{score}%",
            "rating": rating
        }

    def _generate_recommendations(self, word_count: int, keyword_stats: Dict,
                                 heading_analysis: Dict, readability: Dict, text: str) -> List[str]:
        """Generate actionable SEO recommendations"""
        recommendations = []

        # Word count recommendations
        if word_count < 300:
            recommendations.append(f"⚠️ Content too short ({word_count} words). Aim for at least 600 words for better SEO.")
        elif word_count < 600:
            recommendations.append(f"📝 Content length is okay ({word_count} words), but 600-2000 words is ideal for ranking.")

        # Keyword recommendations
        if keyword_stats:
            if not keyword_stats.get("in_h1"):
                recommendations.append(f"🎯 Add target keyword '{keyword_stats['target_keyword']}' to H1 heading")
            if not keyword_stats.get("in_first_paragraph"):
                recommendations.append(f"📍 Include target keyword in the first paragraph")
            if "Too low" in keyword_stats.get("density_status", ""):
                recommendations.append(f"🔑 Increase keyword usage naturally throughout content")
            if "Too high" in keyword_stats.get("density_status", ""):
                recommendations.append(f"⚠️ Reduce keyword usage to avoid keyword stuffing")

        # Heading recommendations
        if heading_analysis.get("h1_count") == 0:
            recommendations.append("❗ Add an H1 heading (critical for SEO)")
        elif heading_analysis.get("h1_count") > 1:
            recommendations.append("❗ Use only one H1 heading per page")
        if heading_analysis.get("h2_count") < 2:
            recommendations.append("📋 Add more H2 subheadings to improve content structure")

        # Readability recommendations
        if readability.get("status") == "Needs improvement":
            recommendations.append("📖 Improve readability: use shorter sentences and simpler words")

        # Content element recommendations
        if not re.search(r'<a\s+href=', text):
            recommendations.append("🔗 Add internal and external links to improve SEO")
        if not re.search(r'<img\s+', text):
            recommendations.append("🖼️ Add relevant images with descriptive alt text")

        # General best practices
        recommendations.append("✅ Use natural language and write for users first, search engines second")
        recommendations.append("✅ Add meta description (150-160 characters) with target keyword")

        return recommendations

    async def check_keyword_density(self, content: str, keywords: List[str]) -> str:
        """Check density for multiple keywords"""
        if not content or not keywords:
            return "Error: content and keywords list are required"

        parser = HTMLTextExtractor()
        try:
            parser.feed(content)
            text_content = parser.get_text()
        except:
            text_content = content

        word_count = len(text_content.split())
        text_lower = text_content.lower()

        results = []
        for keyword in keywords:
            count = text_lower.count(keyword.lower())
            density = round((count / word_count) * 100, 2) if word_count > 0 else 0

            results.append({
                "keyword": keyword,
                "occurrences": count,
                "density": f"{density}%",
                "status": self._get_density_status(density)
            })

        return json.dumps({"word_count": word_count, "keyword_analysis": results}, indent=2)

    async def analyze_headings(self, content: str) -> str:
        """Analyze heading structure"""
        parser = HTMLTextExtractor()
        try:
            parser.feed(content)
            headings = parser.headings
        except:
            return "Error: Invalid HTML content"

        analysis = self._analyze_heading_structure(headings)
        return json.dumps(analysis, indent=2)

    async def check_readability(self, content: str) -> str:
        """Check content readability"""
        parser = HTMLTextExtractor()
        try:
            parser.feed(content)
            text_content = parser.get_text()
        except:
            text_content = content

        word_count = len(text_content.split())
        sentence_count = len(re.findall(r'[.!?]+', text_content))

        readability = self._calculate_readability(text_content, word_count, sentence_count)
        return json.dumps(readability, indent=2)

    async def find_missing_elements(self, content: str) -> str:
        """Find missing SEO elements"""
        missing = []

        if not re.search(r'<h1', content, re.IGNORECASE):
            missing.append("H1 heading")
        if not re.search(r'<h2', content, re.IGNORECASE):
            missing.append("H2 subheadings")
        if not re.search(r'<img.*alt=', content, re.IGNORECASE):
            missing.append("Images with alt text")
        if not re.search(r'<a\s+href=', content, re.IGNORECASE):
            missing.append("Internal/external links")
        if not re.search(r'<meta.*description', content, re.IGNORECASE):
            missing.append("Meta description")

        result = {
            "missing_elements": missing if missing else ["No critical elements missing"],
            "recommendation": "Add missing elements to improve SEO" if missing else "Content structure looks good"
        }

        return json.dumps(result, indent=2)
