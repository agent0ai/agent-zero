"""LLM Router - Manage routing rules"""

import re

from python.helpers.api import ApiHandler
from python.helpers.llm_router import RoutingRule, get_router

# Rule name constraints
_MAX_RULE_NAME_LEN = 64
_RULE_NAME_RE = re.compile(r"^[\w\s\-\.]+$")  # alphanumeric, spaces, hyphens, dots


def _validate_rule_name(name: str | None) -> str | None:
    """Return an error message if the rule name is invalid, else None."""
    if not name or not name.strip():
        return "Rule name is required"
    name = name.strip()
    if len(name) > _MAX_RULE_NAME_LEN:
        return f"Rule name must be {_MAX_RULE_NAME_LEN} characters or fewer"
    if not _RULE_NAME_RE.match(name):
        return "Rule name may only contain letters, numbers, spaces, hyphens, underscores, and dots"
    return None


class LlmRouterRules(ApiHandler):
    """Manage routing rules"""

    async def process(self, input: dict, request) -> dict:
        router = get_router()
        action = input.get("action", "list")

        if action == "list":
            include_disabled = input.get("include_disabled", False)
            rules = router.db.get_routing_rules(enabled_only=not include_disabled)
            return {
                "success": True,
                "rules": [
                    {
                        "name": r.name,
                        "priority": r.priority,
                        "condition": r.condition,
                        "preferredModels": r.preferred_models,
                        "excludedModels": r.excluded_models,
                        "minContextLength": r.min_context_length,
                        "requiredCapabilities": r.required_capabilities,
                        "maxCostPer1k": r.max_cost_per_1k,
                        "maxLatencyMs": r.max_latency_ms,
                        "enabled": r.enabled,
                    }
                    for r in rules
                ],
            }

        elif action == "add":
            rule_data = input.get("rule", {})
            name_error = _validate_rule_name(rule_data.get("name"))
            if name_error:
                return {"success": False, "error": name_error}

            rule = RoutingRule(
                name=rule_data["name"],
                priority=rule_data.get("priority", 0),
                condition=rule_data.get("condition", ""),
                preferred_models=rule_data.get("preferredModels", rule_data.get("preferred_models", [])),
                excluded_models=rule_data.get("excludedModels", rule_data.get("excluded_models", [])),
                min_context_length=rule_data.get("minContextLength", rule_data.get("min_context_length", 0)),
                required_capabilities=rule_data.get("requiredCapabilities", rule_data.get("required_capabilities", [])),
                max_cost_per_1k=rule_data.get("maxCostPer1k", rule_data.get("max_cost_per_1k", 0)),
                max_latency_ms=rule_data.get("maxLatencyMs", rule_data.get("max_latency_ms", 0)),
                enabled=rule_data.get("enabled", True),
            )
            router.add_routing_rule(rule)

            return {"success": True, "message": f"Rule '{rule.name}' added successfully"}

        elif action == "update":
            rule_data = input.get("rule", {})
            if not rule_data.get("name"):
                return {"success": False, "error": "Rule name is required"}

            # Update uses INSERT OR REPLACE (same as add, keyed by unique name)
            rule = RoutingRule(
                name=rule_data["name"],
                priority=rule_data.get("priority", 0),
                condition=rule_data.get("condition", ""),
                preferred_models=rule_data.get("preferredModels", rule_data.get("preferred_models", [])),
                excluded_models=rule_data.get("excludedModels", rule_data.get("excluded_models", [])),
                min_context_length=rule_data.get("minContextLength", rule_data.get("min_context_length", 0)),
                required_capabilities=rule_data.get("requiredCapabilities", rule_data.get("required_capabilities", [])),
                max_cost_per_1k=rule_data.get("maxCostPer1k", rule_data.get("max_cost_per_1k", 0)),
                max_latency_ms=rule_data.get("maxLatencyMs", rule_data.get("max_latency_ms", 0)),
                enabled=rule_data.get("enabled", True),
            )
            router.add_routing_rule(rule)

            return {"success": True, "message": f"Rule '{rule.name}' updated successfully"}

        elif action == "delete":
            name = input.get("name", "")
            if not name:
                return {"success": False, "error": "Rule name is required"}

            deleted = router.db.delete_routing_rule(name)
            if not deleted:
                return {"success": False, "error": f"Rule '{name}' not found"}

            return {"success": True, "message": f"Rule '{name}' deleted successfully"}

        elif action == "toggle":
            name = input.get("name", "")
            enabled = input.get("enabled")
            if not name:
                return {"success": False, "error": "Rule name is required"}
            if enabled is None:
                return {"success": False, "error": "'enabled' field is required"}

            toggled = router.db.toggle_routing_rule(name, bool(enabled))
            if not toggled:
                return {"success": False, "error": f"Rule '{name}' not found"}

            state = "enabled" if enabled else "disabled"
            return {"success": True, "message": f"Rule '{name}' {state} successfully"}

        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}. Valid actions: list, add, update, delete, toggle",
            }
