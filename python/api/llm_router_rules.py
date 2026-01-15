"""LLM Router - Manage routing rules"""

from python.helpers.api import ApiHandler
from python.helpers.llm_router import get_router, RoutingRule


class LlmRouterRules(ApiHandler):
    """Manage routing rules"""

    async def process(self, input: dict, request) -> dict:
        router = get_router()
        action = input.get("action", "list")

        if action == "list":
            rules = router.get_routing_rules()
            return {
                "success": True,
                "rules": [
                    {
                        "name": r.name,
                        "priority": r.priority,
                        "condition": r.condition,
                        "preferred_models": r.preferred_models,
                        "excluded_models": r.excluded_models,
                        "min_context_length": r.min_context_length,
                        "required_capabilities": r.required_capabilities,
                        "max_cost_per_1k": r.max_cost_per_1k,
                        "max_latency_ms": r.max_latency_ms,
                        "enabled": r.enabled
                    }
                    for r in rules
                ]
            }

        elif action == "add":
            rule_data = input.get("rule", {})
            if not rule_data.get("name"):
                return {"success": False, "error": "Rule name is required"}

            rule = RoutingRule(
                name=rule_data["name"],
                priority=rule_data.get("priority", 0),
                condition=rule_data.get("condition", ""),
                preferred_models=rule_data.get("preferred_models", []),
                excluded_models=rule_data.get("excluded_models", []),
                min_context_length=rule_data.get("min_context_length", 0),
                required_capabilities=rule_data.get("required_capabilities", []),
                max_cost_per_1k=rule_data.get("max_cost_per_1k", 0),
                max_latency_ms=rule_data.get("max_latency_ms", 0),
                enabled=rule_data.get("enabled", True)
            )
            router.add_routing_rule(rule)

            return {
                "success": True,
                "message": f"Rule '{rule.name}' added successfully"
            }

        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}"
            }
