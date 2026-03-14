from __future__ import annotations

from datetime import date
from typing import Any

from agent import AgentContext
from python.helpers.api import ApiHandler, Request, Response
from python.helpers.observability_estimator import estimate_portfolio


class ObservabilityUsageEstimate(ApiHandler):
    async def process(self, input: dict[Any, Any], request: Request) -> dict[Any, Any] | Response:
        payload = dict(input or {})
        projects = payload.get("projects")

        if not projects:
            # Fallback profile for "estimate this running instance" without user payload.
            active_contexts = max(len(AgentContext.all()), 1)
            payload = {
                "date": str(date.today()),
                "pricing_profile": {
                    "seat_price_usd": 39,
                    "included_events": 10000,
                    "billing_unit": 1000,
                    "unit_price_usd": 0.5,
                },
                "defaults": {
                    "days_per_month": 30,
                    "growth_buffer_pct": 20,
                    "tool_events_per_turn": 1,
                    "ops_hourly_rate_usd": 120,
                },
                "projects": [
                    {
                        "name": "running-instance",
                        "active_users": active_contexts,
                        "sessions_per_user_per_day": 4,
                        "avg_turns_per_session": 10,
                        "team_seats": active_contexts,
                        "infra_monthly_usd": 250,
                        "ops_hours_per_month": 6,
                    }
                ],
            }

        return {"success": True, "estimate": estimate_portfolio(payload)}
