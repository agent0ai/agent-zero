"""
Rules Parser Tool for SWE Planner Agent
Parses AGENTS.md, CLAUDE.md, and other project guideline files
"""

import re
import os
from python.helpers.tool import Tool, Response
from python.helpers.swe_graph_state import GraphState, CustomRules

class RulesParser(Tool):
    """
    Tool for parsing project-specific rules and guidelines
    """
    
    async def execute(self, **kwargs):
        """Execute rules parsing operations"""
        
        # Get file path or content
        file_path = kwargs.get("file_path")
        file_content = kwargs.get("file_content")
        user_message = kwargs.get("user_message", "")
        
        # First, check if there's AGENTS.md content in the user message
        message_rules = await self.extract_rules_from_message(user_message)
        if message_rules:
            return message_rules
        
        if not file_path and not file_content:
            # Try to find AGENTS.md or CLAUDE.md automatically
            return await self.auto_find_rules(**kwargs)
        
        if file_path and not file_content:
            # Read the file
            try:
                with open(file_path, 'r') as f:
                    file_content = f.read()
            except Exception as e:
                return Response(
                    message=f"Error reading file {file_path}: {str(e)}",
                    break_loop=False
                )
        
        # Parse the content
        return await self.parse_rules_content(file_content, file_path or "provided content")
    
    async def auto_find_rules(self, **kwargs) -> Response:
        """Automatically find and parse rules files"""
        state = self.get_or_create_state()
        
        # Common rule file names
        rule_files = [
            "AGENTS.md",
            "CLAUDE.md",
            ".claude/CLAUDE.md",
            "docs/AGENTS.md",
            "docs/CLAUDE.md",
            ".ai/rules.md",
            "AI_RULES.md"
        ]
        
        found_files = []
        parsed_rules = {}
        
        # Check each potential file
        for rule_file in rule_files:
            if os.path.exists(rule_file):
                found_files.append(rule_file)
                try:
                    with open(rule_file, 'r') as f:
                        content = f.read()
                        rules = self.extract_rules(content)
                        parsed_rules.update(rules)
                except Exception as e:
                    continue
        
        if not found_files:
            return Response(
                message="No rules files found (AGENTS.md, CLAUDE.md, etc.). Proceeding without custom rules.",
                break_loop=False
            )
        
        # Update state with parsed rules
        state.custom_rules = CustomRules(
            rules=parsed_rules,
            source_file=", ".join(found_files)
        )
        state.add_history(f"Parsed rules from: {', '.join(found_files)}")
        self.save_state(state)
        
        rules_summary = self.summarize_rules(parsed_rules)
        
        return Response(
            message=f"Found and parsed rules from {len(found_files)} file(s): {', '.join(found_files)}\n\n{rules_summary}",
            break_loop=False
        )
    
    async def parse_rules_content(self, content: str, source: str) -> Response:
        """Parse rules from provided content"""
        state = self.get_or_create_state()
        
        # Extract rules using various patterns
        rules = self.extract_rules(content)
        
        if not rules:
            return Response(
                message=f"No structured rules found in {source}. Content may need manual interpretation.",
                break_loop=False
            )
        
        # Update state
        state.custom_rules = CustomRules(
            rules=rules,
            source_file=source
        )
        state.add_history(f"Parsed {len(rules)} rules from {source}")
        self.save_state(state)
        
        rules_summary = self.summarize_rules(rules)
        
        return Response(
            message=f"Successfully parsed {len(rules)} rules from {source}:\n\n{rules_summary}",
            break_loop=False
        )
    
    async def extract_rules_from_message(self, user_message: str) -> Response:
        """Extract AGENTS.md content from user message"""
        if not user_message:
            return None
        
        # Look for indicators that the user provided rules in their message
        rule_indicators = [
            "here are the project rules",
            "project rules:",
            "agents.md",
            "claude.md", 
            "development rules",
            "project guidelines",
            "coding standards",
            "<general_rules>",
            "<repository_structure>",
            "<dependencies_and_installation>",
            "<testing_instructions>",
            "<pull_request_formatting>"
        ]
        
        message_lower = user_message.lower()
        has_rule_indicators = any(indicator in message_lower for indicator in rule_indicators)
        
        if not has_rule_indicators:
            return None
        
        # Try to extract rules content
        # Look for content between separators like "---" or after "rules:"
        content_patterns = [
            r'(?:here are the project rules.*?:|project rules.*?:|agents\.md.*?:|claude\.md.*?:)\s*(.*?)(?:\n---|\nNow please|\nPlease implement|\nImplement|\nAdd|\nCreate|\n\n\n|\Z)',
            r'<general_rules>(.*?)</general_rules>',
            r'```(?:md|markdown)?\s*(.*?)\s*```'
        ]
        
        extracted_content = None
        for pattern in content_patterns:
            matches = re.findall(pattern, user_message, re.DOTALL | re.IGNORECASE)
            if matches:
                # Take the longest match as it's likely the most complete
                extracted_content = max(matches, key=len).strip()
                break
        
        if not extracted_content:
            # Fallback: if we have indicators but no clear pattern, 
            # try to extract everything before implementation request
            impl_keywords = ["now please", "implement", "add", "create", "build", "develop"]
            for keyword in impl_keywords:
                if keyword in message_lower:
                    before_impl = user_message[:message_lower.find(keyword)]
                    if len(before_impl) > 100:  # Reasonable length for rules
                        extracted_content = before_impl.strip()
                        break
        
        if not extracted_content or len(extracted_content) < 50:
            return None
        
        # Parse the extracted content
        rules = self.extract_rules(extracted_content)
        
        if not rules:
            # If no structured rules found, treat the whole content as general rules
            rules = {"general_rules": extracted_content}
        
        # Update state
        state = self.get_or_create_state()
        state.custom_rules = CustomRules(
            rules=rules,
            source_file="user message"
        )
        state.add_history(f"Parsed {len(rules)} rules from user message")
        self.save_state(state)
        
        rules_summary = self.summarize_rules(rules)
        
        return Response(
            message=f"Found and parsed project rules from your message ({len(rules)} rule sections):\n\n{rules_summary}",
            break_loop=False
        )
    
    def extract_rules(self, content: str) -> dict:
        """Extract rules from content using various patterns"""
        rules = {}
        
        # Pattern 1: XML-style tags (e.g., <general_rules>...</general_rules>)
        xml_pattern = r'<(\w+)>(.*?)</\1>'
        xml_matches = re.findall(xml_pattern, content, re.DOTALL)
        for tag, value in xml_matches:
            rules[tag] = value.strip()
        
        # Pattern 2: Markdown headers with content
        sections = re.split(r'\n#{1,3}\s+', content)
        for i, section in enumerate(sections):
            if not section:
                continue
            lines = section.split('\n')
            if lines:
                header = lines[0].strip()
                content_lines = lines[1:]
                if header and content_lines:
                    # Normalize header to key
                    key = header.lower().replace(' ', '_').replace('-', '_')
                    rules[key] = '\n'.join(content_lines).strip()
        
        # Pattern 3: Specific rule patterns
        patterns = {
            'repository_structure': r'(?:Repository Structure|Project Structure|File Structure)[\s:]*\n((?:[-*]\s+.*\n?)+)',
            'dependencies': r'(?:Dependencies|Requirements|Installation)[\s:]*\n((?:[-*]\s+.*\n?)+)',
            'testing': r'(?:Testing|Tests|Test Suite)[\s:]*\n((?:[-*]\s+.*\n?)+)',
            'code_style': r'(?:Code Style|Coding Standards|Style Guide)[\s:]*\n((?:[-*]\s+.*\n?)+)',
            'git_workflow': r'(?:Git Workflow|Version Control|Branching)[\s:]*\n((?:[-*]\s+.*\n?)+)',
            'general_rules': r'(?:General Rules|Guidelines|Best Practices)[\s:]*\n((?:[-*]\s+.*\n?)+)'
        }
        
        for key, pattern in patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            if matches and key not in rules:
                rules[key] = '\n'.join(matches).strip()
        
        # Pattern 4: Extract important code blocks
        code_blocks = re.findall(r'```(\w+)?\n(.*?)```', content, re.DOTALL)
        if code_blocks:
            code_examples = {}
            for lang, code in code_blocks:
                if lang:
                    code_examples[lang] = code_examples.get(lang, [])
                    code_examples[lang].append(code.strip())
            if code_examples:
                rules['code_examples'] = str(code_examples)
        
        # Pattern 5: Extract TODO patterns
        todos = re.findall(r'(?:TODO|FIXME|NOTE|IMPORTANT):\s*(.+)', content)
        if todos:
            rules['important_notes'] = '\n'.join(todos)
        
        return rules
    
    def summarize_rules(self, rules: dict) -> str:
        """Create a summary of parsed rules"""
        if not rules:
            return "No rules found."
        
        summary = "Parsed Rules:\n"
        for key, value in rules.items():
            # Truncate long values for summary
            display_value = value[:200] + "..." if len(value) > 200 else value
            # Clean up the display value
            display_value = ' '.join(display_value.split())
            summary += f"\n**{key.replace('_', ' ').title()}**:\n{display_value}\n"
        
        return summary
    
    def get_or_create_state(self) -> GraphState:
        """Get existing state or create new one"""
        state = self.agent.get_data("swe_state")
        
        if not state or not isinstance(state, GraphState):
            state_dict = self.agent.get_data("swe_state_dict")
            if state_dict and isinstance(state_dict, dict):
                state = GraphState.from_dict(state_dict)
            else:
                state = GraphState()
                state.current_agent = "swe-planner"
        
        return state
    
    def save_state(self, state: GraphState):
        """Save state in both formats for reliability"""
        self.agent.set_data("swe_state", state)
        # Also save as dict for backup
        if hasattr(state, 'to_dict'):
            self.agent.set_data("swe_state_dict", state.to_dict())