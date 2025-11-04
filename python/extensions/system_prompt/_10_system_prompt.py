from typing import Any
from python.helpers.extension import Extension
from python.helpers.mcp_handler import MCPConfig
from agent import Agent, LoopData
from python.helpers.settings import get_settings


class SystemPrompt(Extension):

    async def execute(self, system_prompt: list[str] = [], loop_data: LoopData = LoopData(), **kwargs: Any):
        # append main system prompt and tools
        main = get_main_prompt(self.agent)
        tools = get_tools_prompt(self.agent)
        mcp_tools = get_mcp_tools_prompt(self.agent)
        secrets_prompt = get_secrets_prompt(self.agent)

        system_prompt.append(main)
        system_prompt.append(tools)
        if mcp_tools:
            system_prompt.append(mcp_tools)
        if secrets_prompt:
            system_prompt.append(secrets_prompt)


def get_main_prompt(agent: Agent):
    return agent.read_prompt("agent.system.main.md")


def get_tools_prompt(agent: Agent):
    prompt = agent.read_prompt("agent.system.tools.md")
    if agent.config.chat_model.vision:
        prompt += '\n\n' + agent.read_prompt("agent.system.tools_vision.md")
    return prompt


def get_mcp_tools_prompt(agent: Agent):
    mcp_config = MCPConfig.get_instance()
    if mcp_config.servers:
        pre_progress = agent.context.log.progress
        agent.context.log.set_progress("Collecting MCP tools")  # MCP might be initializing, better inform via progress bar
        tools = MCPConfig.get_instance().get_tools_prompt()
        agent.context.log.set_progress(pre_progress)  # return original progress
        return tools
    return ""


def get_secrets_prompt(agent: Agent):
    try:
        # Use lazy import to avoid circular dependencies
        from python.helpers.secrets import SecretsManager
        secrets_manager = SecretsManager.get_instance()
        secrets = secrets_manager.get_secrets_for_prompt()
        vars = get_settings()["variables"]
        return agent.read_prompt("agent.system.secrets.md", secrets=secrets, vars=vars)
    except Exception as e:
        # If secrets module is not available or has issues, return empty string
        return ""
