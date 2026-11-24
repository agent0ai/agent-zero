"""Bind skill declarations to handlers provided by enabled plugins."""

from dataclasses import dataclass, field
from typing import Callable, TYPE_CHECKING

from helpers import extension

if TYPE_CHECKING:
    from helpers.tool import Tool


@dataclass(frozen=True)
class SkillTool:
    plugin: str
    skill_name: str
    factory: Callable[..., "Tool"] = field(compare=False)
    legacy_denials: tuple[str, ...] = ()

    def policy_id(self, name: str) -> str:
        return f"plugin:{self.plugin}:{name}"

    def definition(self, agent, name: str) -> tuple[str, dict] | None:
        from helpers import skills

        if self.skill_name not in skills.get_loaded_skill_names(agent):
            return None
        skill = skills.find_skill(self.skill_name, agent=agent)
        declaration = skill.metadata.get("tool") if skill else None
        if not isinstance(declaration, dict) or declaration.get("name") != name:
            return None
        parameters = declaration.get("parameters")
        if not isinstance(parameters, dict) or parameters.get("type") != "object":
            return None
        return skill.description, parameters


def registered(agent) -> dict[str, SkillTool]:
    bindings: dict[str, SkillTool] = {}
    if getattr(agent, "context", None) is not None:
        extension.call_extensions_sync("skill_tools", agent=agent, bindings=bindings)
    return bindings
