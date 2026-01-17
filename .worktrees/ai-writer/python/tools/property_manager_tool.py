"""
Property Manager Tool
Full rental property management for residential and commercial properties
"""

import sys
from pathlib import Path

from python.helpers.tool import Response, Tool

# Add instruments path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "instruments" / "custom"))


class PropertyManager(Tool):

    async def execute(self, **kwargs):
        """
        Execute property management operations

        Args:
            action (str): Action to perform
            property_id (int): Property ID for specific operations
            tenant_id (int): Tenant ID for tenant operations
            lease_id (int): Lease ID for lease operations
            data (dict): Data for add/update operations
            filters (dict): Filter criteria for list operations
        """

        from property_manager.property_manager import PropertyManager as PM

        action = kwargs.get("action", "dashboard")

        try:
            pm = PM()

            # Dashboard and overview actions
            if action == "dashboard":
                return await self._get_dashboard(pm)

            elif action == "portfolio_summary":
                return await self._get_portfolio_summary(pm)

            elif action == "financials":
                return await self._get_financials(pm, kwargs.get("property_id"), kwargs.get("year"))

            # Property actions
            elif action == "list_properties":
                return await self._list_properties(pm, kwargs.get("filters", {}))

            elif action == "get_property":
                return await self._get_property(pm, kwargs.get("property_id"))

            elif action == "add_property":
                return await self._add_property(pm, kwargs.get("data", {}))

            elif action == "update_property":
                return await self._update_property(pm, kwargs.get("property_id"), kwargs.get("data", {}))

            # Unit actions (for multi-unit properties like motels)
            elif action == "add_units":
                return await self._add_units(pm, kwargs.get("property_id"), kwargs.get("data", {}))

            elif action == "generate_motel_units":
                return await self._generate_motel_units(pm, kwargs.get("property_id"), kwargs.get("data", {}))

            # Tenant actions
            elif action == "add_tenant":
                return await self._add_tenant(pm, kwargs.get("data", {}))

            elif action == "search_tenants":
                return await self._search_tenants(pm, kwargs.get("query", ""))

            elif action == "tenant_history":
                return await self._get_tenant_history(pm, kwargs.get("tenant_id"))

            # Lease actions
            elif action == "create_lease":
                return await self._create_lease(pm, kwargs.get("data", {}))

            elif action == "renew_lease":
                return await self._renew_lease(pm, kwargs.get("lease_id"), kwargs.get("data", {}))

            elif action == "terminate_lease":
                return await self._terminate_lease(pm, kwargs.get("lease_id"), kwargs.get("reason"))

            elif action == "expiring_leases":
                return await self._get_expiring_leases(pm, kwargs.get("days", 30))

            # Rent collection actions
            elif action == "record_payment":
                return await self._record_payment(pm, kwargs.get("data", {}))

            elif action == "rent_roll":
                return await self._get_rent_roll(pm, kwargs.get("month"))

            elif action == "overdue_rent":
                return await self._get_overdue_rent(pm)

            # Expense tracking
            elif action == "record_expense":
                return await self._record_expense(pm, kwargs.get("data", {}))

            elif action == "expense_report":
                return await self._get_expense_report(pm, kwargs.get("property_id"), kwargs.get("data", {}))

            # Maintenance actions
            elif action == "create_maintenance":
                return await self._create_maintenance(pm, kwargs.get("data", {}))

            elif action == "update_maintenance":
                return await self._update_maintenance(pm, kwargs.get("request_id"), kwargs.get("data", {}))

            elif action == "complete_maintenance":
                return await self._complete_maintenance(pm, kwargs.get("request_id"), kwargs.get("data", {}))

            elif action == "maintenance_schedule":
                return await self._get_maintenance_schedule(pm)

            # Cash flow
            elif action == "cash_flow":
                return await self._get_cash_flow(pm, kwargs.get("property_id"), kwargs.get("months", 12))

            # Initial setup
            elif action == "setup_initial":
                return await self._setup_initial_properties(pm)

            else:
                return Response(
                    message=f"""Unknown action: {action}

**Available actions:**
- **Overview**: dashboard, portfolio_summary, financials
- **Properties**: list_properties, get_property, add_property, update_property
- **Units**: add_units, generate_motel_units
- **Tenants**: add_tenant, search_tenants, tenant_history
- **Leases**: create_lease, renew_lease, terminate_lease, expiring_leases
- **Rent**: record_payment, rent_roll, overdue_rent
- **Expenses**: record_expense, expense_report
- **Maintenance**: create_maintenance, update_maintenance, complete_maintenance, maintenance_schedule
- **Financial**: cash_flow
- **Setup**: setup_initial
""",
                    break_loop=False
                )

        except Exception as e:
            return Response(
                message=f"Property Manager error: {e!s}",
                break_loop=False
            )

    # Dashboard and overview
    async def _get_dashboard(self, pm) -> Response:
        """Get property management dashboard"""
        dashboard = pm.get_dashboard()
        summary = dashboard.get("summary", {})
        alerts = dashboard.get("alerts", {})

        result = f"""
## 🏠 Property Management Dashboard

### Portfolio Overview
- **Total Properties**: {summary.get('total_properties', 0)}
- **Total Units**: {summary.get('total_units', 0)}
- **Occupancy Rate**: {summary.get('occupancy_rate', 0):.1f}%
- **Active Leases**: {summary.get('active_leases', 0)}

### Monthly Financial Summary
- **Monthly Rent Income**: ${summary.get('monthly_rent_income', 0):,.2f}
- **Monthly Expenses**: ${summary.get('monthly_expenses', 0):,.2f}
- **Net Cash Flow**: ${summary.get('monthly_rent_income', 0) - summary.get('monthly_expenses', 0):,.2f}

### ⚠️ Alerts
"""

        if alerts.get('expiring_leases', 0) > 0:
            result += f"- **{alerts['expiring_leases']}** leases expiring within 30 days\n"

        if alerts.get('overdue_rent', 0) > 0:
            result += f"- **{alerts['overdue_rent']}** overdue payments (${alerts.get('overdue_amount', 0):,.2f})\n"

        if alerts.get('emergency_maintenance', 0) > 0:
            result += f"- **{alerts['emergency_maintenance']}** emergency maintenance requests\n"

        if alerts.get('open_maintenance', 0) > 0:
            result += f"- **{alerts['open_maintenance']}** open maintenance requests\n"

        # Show critical items
        if dashboard.get('expiring_leases'):
            result += "\n### Expiring Leases\n"
            for lease in dashboard['expiring_leases'][:5]:
                result += f"- {lease['tenant_name']} @ {lease['property_name']} - expires {lease['end_date']}\n"

        if dashboard.get('emergency_maintenance'):
            result += "\n### 🚨 Emergency Maintenance\n"
            for maint in dashboard['emergency_maintenance']:
                result += f"- {maint['title']} @ {maint['property_name']}\n"

        return Response(message=result, break_loop=False)

    async def _get_portfolio_summary(self, pm) -> Response:
        """Get portfolio financial summary"""
        summary = pm.get_portfolio_summary()

        result = """
## 📊 Portfolio Summary

### Properties
| Property | Type | Units | Occupied | Monthly Rent |
|----------|------|-------|----------|--------------|
"""

        for prop in summary.get('properties', []):
            result += f"| {prop['name']} | {prop['type']} | {prop.get('units', 1)} | {prop.get('occupied', 0)} | ${prop.get('monthly_rent', 0):,.2f} |\n"

        result += f"""
### Totals
- **Total Portfolio Value**: ${summary.get('total_value', 0):,.2f}
- **Monthly Income**: ${summary.get('total_monthly_income', 0):,.2f}
- **Annual Income**: ${summary.get('total_annual_income', 0):,.2f}
"""

        return Response(message=result, break_loop=False)

    async def _get_financials(self, pm, property_id: int, year: int) -> Response:
        """Get financial report"""
        if property_id:
            financials = pm.get_property_financials(property_id, year)
        else:
            financials = pm.get_portfolio_financials(year)

        result = f"""
## 💰 Financial Report

### Income
- **Total Rent Collected**: ${financials.get('income', {}).get('total_rent', 0):,.2f}
- **Other Income**: ${financials.get('income', {}).get('other', 0):,.2f}

### Expenses by Category
"""

        for category, amount in financials.get('expenses', {}).get('by_category', {}).items():
            result += f"- **{category.title()}**: ${amount:,.2f}\n"

        result += f"""
### Summary
- **Total Expenses**: ${financials.get('expenses', {}).get('total', 0):,.2f}
- **Net Income**: ${financials.get('net_income', 0):,.2f}
- **ROI**: {financials.get('roi_percent', 0):.1f}%
"""

        return Response(message=result, break_loop=False)

    # Property operations
    async def _list_properties(self, pm, filters: dict) -> Response:
        """List all properties"""
        properties = pm.list_properties(**filters)

        if not properties:
            return Response(message="No properties found", break_loop=False)

        result = f"## 🏠 Properties ({len(properties)})\n\n"

        for prop in properties:
            occupancy = (prop['occupied_units'] / prop['unit_count'] * 100) if prop['unit_count'] > 0 else 0
            result += f"""
### {prop['name']}
- **Type**: {prop['property_type']}
- **Location**: {prop['address']}, {prop['city']}, {prop['state']}
- **Units**: {prop['occupied_units']}/{prop['unit_count']} occupied ({occupancy:.0f}%)
- **Monthly Rent**: ${prop['monthly_rent_total']:,.2f}
- **Status**: {prop['status']}
"""

        return Response(message=result, break_loop=False)

    async def _get_property(self, pm, property_id: int) -> Response:
        """Get property details"""
        if not property_id:
            return Response(message="Error: property_id is required", break_loop=False)

        prop = pm.get_property(property_id)
        if not prop:
            return Response(message=f"Property {property_id} not found", break_loop=False)

        result = f"""
## {prop['name']}

### Basic Information
- **ID**: {prop['id']}
- **Type**: {prop['property_type']}
- **Address**: {prop['address']}
- **City/State**: {prop['city']}, {prop['state']}
- **ZIP**: {prop.get('zip_code', 'N/A')}
- **Status**: {prop['status']}

### Financial
- **Purchase Price**: ${prop.get('purchase_price', 0):,.2f}
- **Market Value**: ${prop.get('market_value', 0):,.2f}
"""

        if prop.get('mortgage'):
            m = prop['mortgage']
            result += f"""
### Mortgage
- **Lender**: {m.get('lender', 'N/A')}
- **Balance**: ${m.get('balance', 0):,.2f}
- **Monthly Payment**: ${m.get('monthly_payment', 0):,.2f}
- **Rate**: {m.get('interest_rate', 0)}%
"""

        if prop.get('units'):
            result += f"\n### Units ({len(prop['units'])})\n"
            for unit in prop['units'][:10]:  # Show first 10
                status_emoji = "🟢" if unit['status'] == 'occupied' else "⚪"
                result += f"- {status_emoji} Unit {unit['unit_number']}: {unit['status']} - ${unit.get('rent_amount', 0):,.2f}/mo\n"
            if len(prop['units']) > 10:
                result += f"... and {len(prop['units']) - 10} more units\n"

        if prop.get('active_leases'):
            result += f"\n### Active Leases ({len(prop['active_leases'])})\n"
            for lease in prop['active_leases']:
                result += f"- {lease.get('tenant_name', 'Unknown')} - ${lease['rent_amount']:,.2f}/mo\n"

        if prop.get('open_maintenance'):
            result += f"\n### Open Maintenance ({len(prop['open_maintenance'])})\n"
            for maint in prop['open_maintenance']:
                priority_emoji = "🚨" if maint['priority'] == 'emergency' else "⚠️" if maint['priority'] == 'high' else "📋"
                result += f"- {priority_emoji} {maint['title']}\n"

        return Response(message=result, break_loop=False)

    async def _add_property(self, pm, data: dict) -> Response:
        """Add a new property"""
        required = ["name", "property_type", "address", "city", "state"]
        missing = [f for f in required if f not in data]
        if missing:
            return Response(
                message=f"Error: Missing required fields: {', '.join(missing)}",
                break_loop=False
            )

        prop = pm.add_property(**data)

        return Response(
            message=f"✅ Property added: **{prop['name']}** (ID: {prop['id']})",
            break_loop=False
        )

    async def _update_property(self, pm, property_id: int, data: dict) -> Response:
        """Update property"""
        if not property_id:
            return Response(message="Error: property_id is required", break_loop=False)

        rows = pm.update_property(property_id, **data)
        if rows:
            return Response(message=f"✅ Property {property_id} updated", break_loop=False)
        return Response(message=f"Property {property_id} not found", break_loop=False)

    # Unit operations
    async def _add_units(self, pm, property_id: int, data: dict) -> Response:
        """Add units to a property"""
        if not property_id:
            return Response(message="Error: property_id is required", break_loop=False)

        units = data.get("units", [])
        if not units:
            return Response(message="Error: units list is required", break_loop=False)

        unit_ids = pm.add_units(property_id, units)
        return Response(
            message=f"✅ Added {len(unit_ids)} units to property {property_id}",
            break_loop=False
        )

    async def _generate_motel_units(self, pm, property_id: int, data: dict) -> Response:
        """Generate motel room units"""
        if not property_id:
            return Response(message="Error: property_id is required", break_loop=False)

        count = data.get("count", 10)
        base_rent = data.get("base_rent", 89.00)

        unit_ids = pm.generate_motel_units(property_id, count, base_rent)
        return Response(
            message=f"✅ Generated {len(unit_ids)} motel rooms at ${base_rent:.2f}/night",
            break_loop=False
        )

    # Tenant operations
    async def _add_tenant(self, pm, data: dict) -> Response:
        """Add a new tenant"""
        required = ["first_name", "last_name"]
        missing = [f for f in required if f not in data]
        if missing:
            return Response(
                message=f"Error: Missing required fields: {', '.join(missing)}",
                break_loop=False
            )

        tenant = pm.add_tenant(**data)
        return Response(
            message=f"✅ Tenant added: **{tenant['first_name']} {tenant['last_name']}** (ID: {tenant['id']})",
            break_loop=False
        )

    async def _search_tenants(self, pm, query: str) -> Response:
        """Search for tenants"""
        if not query:
            return Response(message="Error: query is required", break_loop=False)

        tenants = pm.search_tenants(query)

        if not tenants:
            return Response(message=f"No tenants found matching '{query}'", break_loop=False)

        result = f"## Tenant Search: '{query}' ({len(tenants)} found)\n\n"
        for t in tenants:
            result += f"- **{t['first_name']} {t['last_name']}** - {t.get('email', 'No email')} - {t.get('phone', 'No phone')}\n"

        return Response(message=result, break_loop=False)

    async def _get_tenant_history(self, pm, tenant_id: int) -> Response:
        """Get tenant history"""
        if not tenant_id:
            return Response(message="Error: tenant_id is required", break_loop=False)

        history = pm.get_tenant_history(tenant_id)
        if not history:
            return Response(message=f"Tenant {tenant_id} not found", break_loop=False)

        result = f"""
## Tenant: {history['first_name']} {history['last_name']}

### Contact
- **Email**: {history.get('email', 'N/A')}
- **Phone**: {history.get('phone', 'N/A')}

### Payment History
- **Total Paid**: ${history.get('total_paid', 0):,.2f}

### Leases ({len(history.get('leases', []))})
"""

        for lease in history.get('leases', []):
            result += f"- {lease['property_name']} ({lease['start_date']} - {lease.get('end_date', 'ongoing')}): ${lease['rent_amount']:,.2f}/mo\n"

        return Response(message=result, break_loop=False)

    # Lease operations
    async def _create_lease(self, pm, data: dict) -> Response:
        """Create a new lease"""
        required = ["property_id", "tenant_id", "start_date", "rent_amount"]
        missing = [f for f in required if f not in data]
        if missing:
            return Response(
                message=f"Error: Missing required fields: {', '.join(missing)}",
                break_loop=False
            )

        lease = pm.create_lease(**data)
        return Response(
            message=f"✅ Lease created (ID: {lease['id']}) - ${lease['rent_amount']:,.2f}/mo starting {lease['start_date']}",
            break_loop=False
        )

    async def _renew_lease(self, pm, lease_id: int, data: dict) -> Response:
        """Renew a lease"""
        if not lease_id:
            return Response(message="Error: lease_id is required", break_loop=False)

        new_end_date = data.get("new_end_date")
        if not new_end_date:
            return Response(message="Error: new_end_date is required", break_loop=False)

        pm.renew_lease(lease_id, new_end_date, data.get("new_rent"))
        return Response(
            message=f"✅ Lease {lease_id} renewed until {new_end_date}",
            break_loop=False
        )

    async def _terminate_lease(self, pm, lease_id: int, reason: str) -> Response:
        """Terminate a lease"""
        if not lease_id:
            return Response(message="Error: lease_id is required", break_loop=False)

        pm.terminate_lease(lease_id, reason)
        return Response(
            message=f"✅ Lease {lease_id} terminated",
            break_loop=False
        )

    async def _get_expiring_leases(self, pm, days: int) -> Response:
        """Get expiring leases"""
        leases = pm.get_expiring_leases(days)

        if not leases:
            return Response(message=f"No leases expiring in the next {days} days", break_loop=False)

        result = f"## Leases Expiring in {days} Days ({len(leases)})\n\n"
        for l in leases:
            result += f"- **{l['tenant_name']}** @ {l['property_name']} - expires {l['end_date']} - ${l['rent_amount']:,.2f}/mo\n"

        return Response(message=result, break_loop=False)

    # Rent operations
    async def _record_payment(self, pm, data: dict) -> Response:
        """Record rent payment"""
        required = ["lease_id", "amount"]
        missing = [f for f in required if f not in data]
        if missing:
            return Response(
                message=f"Error: Missing required fields: {', '.join(missing)}",
                break_loop=False
            )

        payment = pm.record_rent_payment(**data)
        return Response(
            message=f"✅ Payment recorded: ${payment['amount']:,.2f}",
            break_loop=False
        )

    async def _get_rent_roll(self, pm, month: str) -> Response:
        """Get rent roll"""
        roll = pm.get_rent_roll(month)

        if not roll:
            return Response(message="No active leases found", break_loop=False)

        total_expected = sum(r['expected'] for r in roll)
        total_paid = sum(r['paid'] for r in roll)
        total_balance = sum(r['balance'] for r in roll)

        result = f"""
## Rent Roll - {month or 'Current Month'}

| Property | Unit | Tenant | Expected | Paid | Balance |
|----------|------|--------|----------|------|---------|
"""

        for r in roll:
            unit = r.get('unit_number', '-')
            result += f"| {r['property_name']} | {unit} | {r['tenant_name']} | ${r['expected']:,.2f} | ${r['paid']:,.2f} | ${r['balance']:,.2f} |\n"

        result += f"""
### Totals
- **Expected**: ${total_expected:,.2f}
- **Collected**: ${total_paid:,.2f}
- **Outstanding**: ${total_balance:,.2f}
"""

        return Response(message=result, break_loop=False)

    async def _get_overdue_rent(self, pm) -> Response:
        """Get overdue rent"""
        overdue = pm.get_overdue_rent()

        if not overdue:
            return Response(message="✅ No overdue rent payments!", break_loop=False)

        total = sum(p['amount'] for p in overdue)

        result = f"## ⚠️ Overdue Rent ({len(overdue)} payments - ${total:,.2f})\n\n"
        for p in overdue:
            result += f"- **{p.get('tenant_name', 'Unknown')}** - ${p['amount']:,.2f} due {p['due_date']}\n"

        return Response(message=result, break_loop=False)

    # Expense operations
    async def _record_expense(self, pm, data: dict) -> Response:
        """Record expense"""
        required = ["property_id", "category", "description", "amount"]
        missing = [f for f in required if f not in data]
        if missing:
            return Response(
                message=f"Error: Missing required fields: {', '.join(missing)}",
                break_loop=False
            )

        expense = pm.record_expense(**data)
        return Response(
            message=f"✅ Expense recorded: ${expense['amount']:,.2f} - {expense['description']}",
            break_loop=False
        )

    async def _get_expense_report(self, pm, property_id: int, data: dict) -> Response:
        """Get expense report"""
        if not property_id:
            return Response(message="Error: property_id is required", break_loop=False)

        report = pm.get_expense_report(property_id, data.get('start_date'), data.get('end_date'))

        result = f"""
## Expense Report - Property {property_id}

### By Category
| Category | Total |
|----------|-------|
"""

        for cat, info in report.get('by_category', {}).items():
            result += f"| {cat.title()} | ${info['total']:,.2f} |\n"

        result += f"""
### Summary
- **Total Expenses**: ${report.get('total', 0):,.2f}
- **Expense Count**: {report.get('expense_count', 0)}
"""

        return Response(message=result, break_loop=False)

    # Maintenance operations
    async def _create_maintenance(self, pm, data: dict) -> Response:
        """Create maintenance request"""
        required = ["property_id", "category", "title"]
        missing = [f for f in required if f not in data]
        if missing:
            return Response(
                message=f"Error: Missing required fields: {', '.join(missing)}",
                break_loop=False
            )

        request = pm.create_maintenance_request(**data)
        priority_emoji = "🚨" if data.get('priority') == 'emergency' else "⚠️" if data.get('priority') == 'high' else "📋"
        return Response(
            message=f"{priority_emoji} Maintenance request created (ID: {request['id']}): {request['title']}",
            break_loop=False
        )

    async def _update_maintenance(self, pm, request_id: int, data: dict) -> Response:
        """Update maintenance request"""
        if not request_id:
            return Response(message="Error: request_id is required", break_loop=False)

        status = data.get("status", "in_progress")
        pm.update_maintenance_status(request_id, status, **data)
        return Response(
            message=f"✅ Maintenance request {request_id} updated to '{status}'",
            break_loop=False
        )

    async def _complete_maintenance(self, pm, request_id: int, data: dict) -> Response:
        """Complete maintenance request"""
        if not request_id:
            return Response(message="Error: request_id is required", break_loop=False)

        actual_cost = data.get("actual_cost", 0)
        pm.complete_maintenance(request_id, actual_cost, data.get("notes"))
        return Response(
            message=f"✅ Maintenance request {request_id} completed - Cost: ${actual_cost:,.2f}",
            break_loop=False
        )

    async def _get_maintenance_schedule(self, pm) -> Response:
        """Get maintenance schedule"""
        schedule = pm.get_maintenance_schedule()

        if not schedule:
            return Response(message="No scheduled maintenance", break_loop=False)

        result = f"## 🔧 Scheduled Maintenance ({len(schedule)})\n\n"
        for m in schedule:
            result += f"- **{m['scheduled_date']}**: {m['title']} @ {m['property_name']}\n"

        return Response(message=result, break_loop=False)

    # Cash flow
    async def _get_cash_flow(self, pm, property_id: int, months: int) -> Response:
        """Get cash flow projection"""
        if not property_id:
            return Response(message="Error: property_id is required", break_loop=False)

        projections = pm.get_cash_flow_projection(property_id, months)

        if not projections:
            return Response(message="Unable to generate projections", break_loop=False)

        result = f"## 📈 Cash Flow Projection ({months} months)\n\n"
        result += "| Month | Income | Expenses | Net |\n"
        result += "|-------|--------|----------|-----|\n"

        for p in projections:
            result += f"| {p['month']} | ${p['expected_income']:,.2f} | ${p['expected_expenses']:,.2f} | ${p['projected_net']:,.2f} |\n"

        total_net = sum(p['projected_net'] for p in projections)
        result += f"\n**Total Projected Net**: ${total_net:,.2f}"

        return Response(message=result, break_loop=False)

    # Initial setup
    async def _setup_initial_properties(self, pm) -> Response:
        """Set up initial properties"""
        from property_manager.property_manager import seed_initial_properties

        seed_initial_properties(pm)

        return Response(
            message="""
✅ **Initial Properties Created**

The following properties have been added to your portfolio:

1. **West Bethel Motel** (Bethel, ME) - Commercial/Motel
   - 10 rooms generated at $89/night base rate

2. **House 1** - Residential (Update address)
3. **House 2** - Residential (Update address)
4. **House 3** - Residential (Update address)

**Next Steps:**
1. Update house addresses using: `action: update_property, property_id: X, data: {address: "...", city: "...", state: "..."}`
2. Add tenants: `action: add_tenant, data: {first_name: "...", last_name: "...", email: "...", phone: "..."}`
3. Create leases: `action: create_lease, data: {property_id: X, tenant_id: Y, start_date: "YYYY-MM-DD", rent_amount: 1000}`
""",
            break_loop=False
        )
