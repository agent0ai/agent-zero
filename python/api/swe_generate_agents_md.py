"""
API endpoint for generating AGENTS.md files using the SWE system
"""

from agent import Agent, AgentConfig, UserMessage
from python.helpers.api import ApiHandler, Request, Response
from python.helpers.settings import get_settings
from python.helpers import files
import models

class SweGenerateAgentsMd(ApiHandler):
    """
    Generate AGENTS.md file based on project information
    """
    
    @classmethod
    def requires_auth(cls) -> bool:
        return True
    
    @classmethod 
    def requires_csrf(cls) -> bool:
        return True
        
    async def process(self, input: dict, request: Request) -> dict | Response:
        """Process the AGENTS.md generation request"""
        
        try:
            # Extract form data
            project_description = input.get("project_description", "").strip()
            tech_stack = input.get("tech_stack", "").strip()
            coding_standards = input.get("coding_standards", "").strip()
            testing_approach = input.get("testing_approach", "").strip()
            
            if not project_description:
                return {
                    "success": False,
                    "error": "Project description is required"
                }
            
            # Create the generation prompt
            generation_prompt = self._create_generation_prompt(
                project_description=project_description,
                tech_stack=tech_stack,
                coding_standards=coding_standards,
                testing_approach=testing_approach
            )
            
            # Create a utility agent for generation
            agent = await self._create_utility_agent()
            
            # Generate the AGENTS.md content
            agent.hist_add_user_message(UserMessage(message=generation_prompt))
            result = await agent.monologue()
            
            # Extract the actual AGENTS.md content from the agent's response
            agents_md_content = self._extract_agents_md_content(result, agent)
            
            return {
                "success": True,
                "agents_md_content": agents_md_content,
                "suggested_filename": "AGENTS.md"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _create_generation_prompt(self, project_description: str, tech_stack: str, 
                                 coding_standards: str, testing_approach: str) -> str:
        """Create the prompt for AGENTS.md generation"""
        
        agents_md_template = """
Generate project development rules based on the following information, then create an AGENTS.md file:

**Project Description**: {project_description}

**Technology Stack**: {tech_stack}

**Coding Standards**: {coding_standards}

**Testing Approach**: {testing_approach}

---

Based on this information, please analyze this repository (if accessible) and create an AGENTS.md file with the following structure. Ensure each section is wrapped in the specified XML tags:

<general_rules>
- Include development workflow rules
- Mention linting/formatting commands if applicable
- Code organization patterns
- Any project-specific conventions
- Common scripts and build commands
</general_rules>

<repository_structure>
- High-level directory organization
- Key folders and their purposes
- App/service/package structure
- Important configuration files
</repository_structure>

<dependencies_and_installation>
- Package manager and installation steps
- Environment setup requirements
- Any special configuration needed
</dependencies_and_installation>

<testing_instructions>
- Testing framework in use
- How to run tests
- Test file organization
- Coverage requirements
</testing_instructions>

<pull_request_formatting>
- Only include if specific PR formatting rules exist in the repo
- Leave empty if no specific requirements found
</pull_request_formatting>

Create a complete AGENTS.md file that any developer (or AI agent) could use to understand how to work with this codebase effectively. Focus on practical, actionable guidelines that will help maintain code quality and consistency.
""".format(
            project_description=project_description,
            tech_stack=tech_stack or "Not specified",
            coding_standards=coding_standards or "Standard best practices",
            testing_approach=testing_approach or "Standard testing practices"
        )
        
        return agents_md_template
    
    def _extract_agents_md_content(self, result: str, agent: Agent) -> str:
        """Extract AGENTS.md content from agent response"""
        
        # First, try to find content in the agent's conversation history
        # Look for the actual generated content in the last AI message
        if agent and hasattr(agent, 'history'):
            try:
                # Get the history output
                history_messages = agent.history.output()
                
                # Get the last AI message which should contain the generated content
                for message in reversed(history_messages):
                    if hasattr(message, 'content') and message.content:
                        # Extract text content from the message
                        content = ""
                        if isinstance(message.content, dict):
                            content = message.content.get('text', '') or message.content.get('message', '')
                        elif isinstance(message.content, str):
                            content = message.content
                        
                        if content and any(tag in content for tag in ['<general_rules>', '<repository_structure>', 
                                                         '<dependencies_and_installation>', '<testing_instructions>',
                                                         '<pull_request_formatting>', '# AGENTS.md']):
                            
                            # Clean up the content - remove any agent meta-commentary
                            lines = content.split('\n')
                            cleaned_lines = []
                            in_agents_md = False
                            
                            for line in lines:
                                # Start capturing when we see AGENTS.md content
                                if ('# AGENTS.md' in line or 
                                    '<general_rules>' in line or 
                                    line.strip().startswith('# ') and 'Development Rulebook' in line):
                                    in_agents_md = True
                                
                                # Skip agent meta-commentary
                                if (in_agents_md and 
                                    not line.startswith('I have successfully') and
                                    not line.startswith('The task is now complete') and
                                    not line.startswith('What would you like to do')):
                                    cleaned_lines.append(line)
                            
                            if cleaned_lines:
                                return '\n'.join(cleaned_lines).strip()
            except Exception as e:
                # If history parsing fails, fall through to use the result directly
                print(f"Warning: Could not parse agent history: {e}")
        
        # Fallback: if no structured content found, return the result
        # but try to clean it up
        if result:
            lines = result.split('\n')
            cleaned_lines = []
            
            for line in lines:
                # Skip agent meta-commentary
                if (not line.startswith('I have successfully') and
                    not line.startswith('The task is now complete') and
                    not line.startswith('What would you like to do')):
                    cleaned_lines.append(line)
            
            return '\n'.join(cleaned_lines).strip()
        
        return "# AGENTS.md\n\nDevelopment rules could not be extracted from the agent response."
    
    async def _create_utility_agent(self) -> Agent:
        """Create a utility agent for generation"""
        
        # Use the standard initialization approach
        from initialize import initialize_agent
        from python.helpers import runtime
        
        # Get config from standard initialization
        config = initialize_agent()
        
        # Set profile for generation
        config.profile = "default"
        
        # Create context for generation
        context_id = f"swe_gen_{runtime.get_runtime_id()}"
        
        # Import AgentContext 
        from agent import AgentContext
        context = AgentContext(config=config, id=context_id)
        
        # Create the agent with proper initialization
        agent = Agent(number=0, config=config, context=context)
        
        return agent