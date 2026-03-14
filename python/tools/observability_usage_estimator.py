from __future__ import annotations

import json
from datetime import date

from python.helpers.observability_estimator import estimate_portfolio
from python.helpers.tool import Response, Tool


class ObservabilityUsageEstimator(Tool):
    async def execute(self, **kwargs):
        """
        Estimate observability usage/cost across one or more projects.

        Args:
            payload_json: Optional JSON string with pricing/defaults/projects.
        """
        payload_json = self.args.get("payload_json", "").strip()
        payload = {}
        if payload_json:
            try:
                payload = json.loads(payload_json)
            except Exception as e:
                return Response(message=f"Invalid payload_json: {e}", break_loop=False)
        else:
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
                        "name": "default-project",
                        "active_users": 5,
                        "sessions_per_user_per_day": 4,
                        "avg_turns_per_session": 10,
                        "team_seats": 5,
                        "infra_monthly_usd": 250,
                        "ops_hours_per_month": 6,
                    }
                ],
            }

        result = estimate_portfolio(payload)
        return Response(message=json.dumps(result, indent=2), break_loop=False)
