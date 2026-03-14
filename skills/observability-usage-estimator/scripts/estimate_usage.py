#!/usr/bin/env python3
import argparse
import json
from dataclasses import dataclass


@dataclass
class PricingProfile:
    seat_price_usd: float
    included_events: float
    billing_unit: float
    unit_price_usd: float


def _float(v, default=0.0):
    try:
        return float(v)
    except Exception:
        return float(default)


def estimate_project(project: dict, defaults: dict, pricing: PricingProfile) -> dict:
    days_per_month = _float(project.get("days_per_month", defaults.get("days_per_month", 30)), 30)
    growth_buffer_pct = _float(project.get("growth_buffer_pct", defaults.get("growth_buffer_pct", 20)), 20)
    tool_events_per_turn = _float(project.get("tool_events_per_turn", defaults.get("tool_events_per_turn", 1)), 1)
    ops_hourly_rate_usd = _float(project.get("ops_hourly_rate_usd", defaults.get("ops_hourly_rate_usd", 120)), 120)

    active_users = _float(project.get("active_users", 0))
    sessions_per_user_per_day = _float(project.get("sessions_per_user_per_day", 0))
    avg_turns_per_session = _float(project.get("avg_turns_per_session", 0))
    team_seats = _float(project.get("team_seats", 0))
    infra_monthly_usd = _float(project.get("infra_monthly_usd", 0))
    ops_hours_per_month = _float(project.get("ops_hours_per_month", 0))

    sessions = active_users * sessions_per_user_per_day * days_per_month
    turns = sessions * avg_turns_per_session
    trace_events = turns * max(tool_events_per_turn, 1)
    buffered_events = trace_events * (1 + (growth_buffer_pct / 100.0))

    commercial_fixed_usd = team_seats * pricing.seat_price_usd
    billable_events = max(buffered_events - pricing.included_events, 0)
    commercial_variable_usd = (billable_events / pricing.billing_unit) * pricing.unit_price_usd
    commercial_total_usd = commercial_fixed_usd + commercial_variable_usd

    ops_labor_usd = ops_hours_per_month * ops_hourly_rate_usd
    self_hosted_total_usd = infra_monthly_usd + ops_labor_usd

    if pricing.unit_price_usd > 0:
        break_even_events = (
            (self_hosted_total_usd - commercial_fixed_usd) / pricing.unit_price_usd
        ) * pricing.billing_unit + pricing.included_events
    else:
        break_even_events = None

    return {
        "name": project.get("name", "unknown"),
        "sessions": round(sessions, 2),
        "turns": round(turns, 2),
        "buffered_events": round(buffered_events, 2),
        "commercial_total_usd": round(commercial_total_usd, 2),
        "self_hosted_total_usd": round(self_hosted_total_usd, 2),
        "break_even_events": round(break_even_events, 2) if break_even_events is not None else None,
    }


def main():
    parser = argparse.ArgumentParser(description="Estimate observability usage and costs.")
    parser.add_argument("--input", required=True, help="Path to estimation input JSON")
    args = parser.parse_args()

    with open(args.input, encoding="utf-8") as f:
        payload = json.load(f)

    pricing_raw = payload.get("pricing_profile", {})
    pricing = PricingProfile(
        seat_price_usd=_float(pricing_raw.get("seat_price_usd", 0)),
        included_events=_float(pricing_raw.get("included_events", 0)),
        billing_unit=_float(pricing_raw.get("billing_unit", 1000)),
        unit_price_usd=_float(pricing_raw.get("unit_price_usd", 0)),
    )

    defaults = payload.get("defaults", {})
    projects = payload.get("projects", [])

    project_estimates = [estimate_project(p, defaults, pricing) for p in projects]
    totals = {
        "buffered_events": round(sum(p["buffered_events"] for p in project_estimates), 2),
        "commercial_total_usd": round(sum(p["commercial_total_usd"] for p in project_estimates), 2),
        "self_hosted_total_usd": round(sum(p["self_hosted_total_usd"] for p in project_estimates), 2),
    }

    output = {
        "date": payload.get("date"),
        "project_count": len(project_estimates),
        "projects": project_estimates,
        "totals": totals,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
