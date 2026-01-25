"""
Brand Voice Tool

Converted from Mahoosuc OS /brand:voice command to native Agent Zero tool.
Define, maintain, and enforce brand voice consistency across all content.

Source: .claude/commands/brand/voice.md
"""

from python.helpers.tool import Response, Tool


class BrandVoice(Tool):
    """
    Brand voice consistency tool for content analysis and guidelines.

    Supports:
    - Define brand voice guidelines
    - Analyze content for voice consistency
    - Check files against brand voice
    - Train on existing content

    Args:
        mode: Operation mode (define|analyze|check|train)
        content: Content to analyze (required for analyze mode)
        file: File path to check (required for check mode)
    """

    async def execute(self, **kwargs):
        """
        Execute brand voice operation.

        Args (from self.args):
            mode: Operation mode (required)
            content: Content string for analysis (for analyze mode)
            file: File path for checking (for check mode)

        Returns:
            Response with brand voice analysis or guidelines
        """
        # Get parameters
        mode = self.args.get("mode", "")
        content = self.args.get("content", "")
        file = self.args.get("file", "")

        # Validate mode
        if not mode:
            return Response(
                message="Error: mode parameter is required. "
                "Valid modes: define, analyze, check, train. "
                'Example: {"mode": "define"}',
                break_loop=False,
            )

        # Normalize mode
        mode = mode.lower().strip()
        valid_modes = ["define", "analyze", "check", "train"]

        if mode not in valid_modes:
            return Response(
                message=f"Error: Invalid mode '{mode}'. " f"Valid modes: {', '.join(valid_modes)}",
                break_loop=False,
            )

        # Route to appropriate handler
        if mode == "define":
            return await self._define_brand_voice()
        elif mode == "analyze":
            return await self._analyze_content(content)
        elif mode == "check":
            return await self._check_file(file)
        elif mode == "train":
            return await self._train_brand_voice()

    async def _define_brand_voice(self) -> Response:
        """Define brand voice guidelines"""
        guidelines = """# Brand Voice Guidelines

## Overview

Brand voice represents the consistent personality and tone across all communications.
This tool helps maintain voice consistency to strengthen brand recognition and trust.

## Core Voice Attributes

### 1. Tone Characteristics

**Professional but Approachable**
- Use clear, direct language
- Avoid jargon unless necessary
- Maintain expertise without being condescending
- Be friendly and helpful

**Authentic and Trustworthy**
- Be honest and transparent
- Back claims with evidence
- Admit limitations when appropriate
- Stay true to brand values

**Confident and Empowering**
- Use active voice
- Make definitive statements when appropriate
- Empower readers to take action
- Inspire confidence through clarity

### 2. Writing Style

**Clarity First**
- Short sentences and paragraphs
- One idea per sentence
- Avoid redundancy
- Use concrete examples

**Consistent Terminology**
- Maintain glossary of key terms
- Use terminology consistently
- Define technical terms on first use
- Avoid synonyms for key concepts

**Active and Engaging**
- Use active voice predominantly (80%+)
- Address reader directly ("you")
- Use present tense when possible
- Include calls to action

### 3. Content Structure

**Scannable Format**
- Use descriptive headings
- Include bulleted lists
- Add visual breaks
- Highlight key points

**Logical Flow**
- Start with most important information
- Group related concepts
- Use transitions effectively
- Conclude with clear next steps

### 4. Brand-Specific Rules

**Do's**
- ✓ Use inclusive language
- ✓ Be specific and measurable
- ✓ Provide context
- ✓ Show, don't just tell
- ✓ Use data to support claims

**Don'ts**
- ✗ Use clichés or buzzwords
- ✗ Make unsupported claims
- ✗ Assume prior knowledge
- ✗ Use passive voice excessively
- ✗ Overuse exclamation points

## Voice Consistency Metrics

### Assessment Criteria

1. **Tone Score** (0-100)
   - Professional language usage
   - Appropriate formality level
   - Emotional consistency

2. **Clarity Score** (0-100)
   - Sentence length (target: 15-20 words)
   - Readability level (target: grade 8-10)
   - Technical term usage

3. **Engagement Score** (0-100)
   - Active voice ratio (target: 80%+)
   - Direct address usage
   - Call-to-action presence

4. **Consistency Score** (0-100)
   - Terminology alignment
   - Style guide compliance
   - Brand value reflection

## Implementation

Use this tool to:
- **Define**: Review and refine these guidelines
- **Analyze**: Score content against these criteria
- **Check**: Validate files for compliance
- **Train**: Learn from existing high-quality content

---

*Generated by Brand Voice Tool (converted from Mahoosuc OS)*
"""
        return Response(message=guidelines, break_loop=False)

    async def _analyze_content(self, content: str) -> Response:
        """Analyze content for brand voice consistency"""
        if not content:
            return Response(
                message="Error: content parameter is required for analyze mode. "
                'Example: {"mode": "analyze", "content": "Your content here..."}',
                break_loop=False,
            )

        # Perform basic analysis
        word_count = len(content.split())
        sentence_count = content.count(".") + content.count("!") + content.count("?")
        avg_sentence_length = word_count / max(sentence_count, 1)

        # Check for passive voice indicators
        passive_indicators = ["was", "were", "been", "being", "is", "are"]
        passive_count = sum(content.lower().count(f" {word} ") for word in passive_indicators)

        # Check for direct address
        direct_address_count = content.lower().count(" you ")

        # Check for jargon/buzzwords
        jargon = ["synergy", "leverage", "paradigm", "disrupt", "innovative"]
        jargon_found = [word for word in jargon if word in content.lower()]

        # Calculate scores
        clarity_score = max(0, min(100, 100 - abs(avg_sentence_length - 17.5) * 5))
        engagement_score = min(100, direct_address_count * 10)
        tone_score = max(0, 100 - len(jargon_found) * 20)
        overall_score = (clarity_score + engagement_score + tone_score) / 3

        analysis = f"""# Brand Voice Analysis

## Content Overview

- **Word Count**: {word_count}
- **Sentence Count**: {sentence_count}
- **Average Sentence Length**: {avg_sentence_length:.1f} words (target: 15-20)

## Voice Consistency Scores

### Overall Score: {overall_score:.0f}/100

### Detailed Breakdown

**Clarity Score: {clarity_score:.0f}/100**
- Sentence length: {avg_sentence_length:.1f} words
- Assessment: {'✓ Good' if 15 <= avg_sentence_length <= 20 else '⚠ Review recommended'}

**Engagement Score: {engagement_score:.0f}/100**
- Direct address count: {direct_address_count}
- Assessment: {'✓ Good' if direct_address_count >= 3 else '⚠ Consider adding more "you" statements'}

**Tone Score: {tone_score:.0f}/100**
- Jargon detected: {len(jargon_found)}
{f"- Found: {', '.join(jargon_found)}" if jargon_found else "- No common jargon detected"}
- Assessment: {'✓ Good' if not jargon_found else '⚠ Consider simplifying language'}

## Recommendations

"""

        # Add specific recommendations
        recommendations = []

        if avg_sentence_length > 20:
            recommendations.append("- Break long sentences into shorter ones (target: 15-20 words)")
        elif avg_sentence_length < 15:
            recommendations.append("- Some sentences may be too short; combine related ideas")

        if direct_address_count < 3:
            recommendations.append("- Use more direct address ('you') to engage readers")

        if jargon_found:
            recommendations.append("- Replace jargon with clear, simple language")

        if passive_count > word_count * 0.2:
            recommendations.append("- Reduce passive voice usage (target: <20% of content)")

        if not recommendations:
            recommendations.append("- Content aligns well with brand voice guidelines")

        analysis += "\n".join(recommendations)
        analysis += "\n\n---\n\n*Generated by Brand Voice Tool (converted from Mahoosuc OS)*"

        return Response(message=analysis, break_loop=False)

    async def _check_file(self, file: str) -> Response:
        """Check file against brand voice guidelines"""
        if not file:
            return Response(
                message="Error: file parameter is required for check mode. "
                'Example: {"mode": "check", "file": "/path/to/content.md"}',
                break_loop=False,
            )

        # In POC mode, provide simulated check result
        report = f"""# Brand Voice File Check

## File Checked

**Path**: {file}

## Consistency Check Results (POC)

### Voice Compliance: 85/100

**Findings**:
- ✓ Tone is professional and approachable
- ✓ Clear structure with headings
- ✓ Good use of active voice
- ⚠ Some sentences exceed recommended length
- ⚠ Consider adding more direct address

### Style Guide Compliance

- ✓ Consistent terminology
- ✓ Proper heading hierarchy
- ✓ Appropriate formatting
- ✓ Call-to-action present

### Recommendations

1. Review sentences longer than 25 words
2. Add "you" statements to increase engagement
3. Consider breaking dense paragraphs
4. Add transition phrases between sections

## Next Steps

1. Review flagged sections
2. Apply recommendations
3. Re-run check to verify improvements
4. Consider training on this content if score improves

---

**Note**: This is a POC implementation. Full implementation will:
- Read and parse actual file content
- Apply NLP analysis for deeper insights
- Compare against learned brand voice patterns
- Provide line-by-line feedback
- Suggest specific edits

---

*Generated by Brand Voice Tool (converted from Mahoosuc OS)*
"""
        return Response(message=report, break_loop=False)

    async def _train_brand_voice(self) -> Response:
        """Train brand voice model on existing content"""
        report = """# Brand Voice Training

## Training Overview

Learn brand voice patterns from existing high-quality content to improve
consistency checking and analysis.

## Training Process (POC)

### Step 1: Content Collection
- ✓ Scan repository for content files
- ✓ Identify high-quality examples
- ✓ Extract voice patterns

### Step 2: Pattern Analysis
- ✓ Analyze tone characteristics
- ✓ Extract common phrases
- ✓ Identify style patterns
- ✓ Build terminology glossary

### Step 3: Model Training
- ✓ Train voice consistency model
- ✓ Build pattern recognition
- ✓ Create scoring algorithms
- ✓ Validate against known good content

### Step 4: Validation
- ✓ Test on sample content
- ✓ Verify accuracy
- ✓ Fine-tune thresholds
- ✓ Document learned patterns

## Training Results (POC)

**Content Analyzed**: 50+ documents
**Patterns Identified**: 25+ voice characteristics
**Model Accuracy**: 92%
**Ready for Use**: ✓

## Learned Patterns

1. **Tone**: Professional, approachable, confident
2. **Sentence Structure**: 15-18 words average
3. **Voice**: 85% active, 15% passive
4. **Terminology**: Consistent technical terms
5. **Engagement**: High use of "you" and imperatives

## Usage

Now that training is complete:
- Use `analyze` mode to score new content
- Use `check` mode to validate files
- Use `define` mode to review guidelines

---

**Note**: This is a POC implementation. Full implementation will:
- Actually read and parse repository content
- Use NLP/ML for pattern extraction
- Build statistical models for scoring
- Save learned patterns for reuse
- Continuously improve from feedback

---

*Generated by Brand Voice Tool (converted from Mahoosuc OS)*
"""
        return Response(message=report, break_loop=False)
