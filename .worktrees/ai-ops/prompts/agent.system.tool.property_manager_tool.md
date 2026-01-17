# Property Manager Tool

A comprehensive rental property management tool for managing residential and commercial properties, including tenants, leases, rent collection, maintenance, and financial reporting.

## Purpose

The Property Manager tool helps you:
- Track multiple properties (houses, apartments, motels, commercial)
- Manage tenants and lease agreements
- Collect and track rent payments
- Handle maintenance requests
- Track expenses and calculate ROI
- Generate financial reports

## Your Properties

Currently configured properties:
- **West Bethel Motel** - Commercial/Motel in Bethel, ME
- **House 1, 2, 3** - Residential properties (update addresses when known)

## Usage

### Dashboard

Get a complete overview of your property portfolio:

```python
property_manager_tool(action="dashboard")
```

Shows:
- Total properties and units
- Occupancy rate
- Monthly income/expenses
- Alerts (expiring leases, overdue rent, maintenance)
- Critical items requiring attention

### Portfolio Summary

View financial summary across all properties:

```python
property_manager_tool(action="portfolio_summary")
```

### Initial Setup

Set up your initial properties (West Bethel Motel + 3 houses):

```python
property_manager_tool(action="setup_initial")
```

## Property Management

### List Properties

```python
property_manager_tool(
    action="list_properties",
    filters={
        "property_type": "house",    # Optional: house, apartment, motel, commercial
        "status": "active"           # Optional: active, inactive, for_sale
    }
)
```

### Get Property Details

```python
property_manager_tool(
    action="get_property",
    property_id=1
)
```

### Add Property

```python
property_manager_tool(
    action="add_property",
    data={
        "name": "Beach House",
        "property_type": "house",
        "address": "123 Ocean Drive",
        "city": "Portland",
        "state": "ME",
        "zip_code": "04101",
        "purchase_price": 350000,
        "market_value": 400000,
        "notes": "3BR, 2BA oceanfront property"
    }
)
```

Property types: `house`, `apartment`, `condo`, `townhouse`, `duplex`, `motel`, `commercial`, `mixed_use`

### Update Property

```python
property_manager_tool(
    action="update_property",
    property_id=1,
    data={
        "address": "456 Main Street",
        "market_value": 425000
    }
)
```

## Unit Management (Multi-Unit Properties)

### Generate Motel Units

Automatically create numbered units for a motel:

```python
property_manager_tool(
    action="generate_motel_units",
    property_id=1,
    data={
        "count": 20,           # Number of rooms
        "base_rent": 89.00     # Nightly rate
    }
)
```

### Add Custom Units

```python
property_manager_tool(
    action="add_units",
    property_id=1,
    data={
        "units": [
            {"unit_number": "101", "bedrooms": 1, "bathrooms": 1, "rent_amount": 1200},
            {"unit_number": "102", "bedrooms": 2, "bathrooms": 1, "rent_amount": 1500}
        ]
    }
)
```

## Tenant Management

### Add Tenant

```python
property_manager_tool(
    action="add_tenant",
    data={
        "first_name": "John",
        "last_name": "Smith",
        "email": "john.smith@email.com",
        "phone": "207-555-1234",
        "emergency_contact_name": "Jane Smith",
        "emergency_contact_phone": "207-555-5678"
    }
)
```

### Search Tenants

```python
property_manager_tool(
    action="search_tenants",
    query="Smith"
)
```

### View Tenant History

```python
property_manager_tool(
    action="tenant_history",
    tenant_id=1
)
```

## Lease Management

### Create Lease

```python
property_manager_tool(
    action="create_lease",
    data={
        "property_id": 1,
        "tenant_id": 1,
        "unit_id": 1,              # Optional: for multi-unit properties
        "start_date": "2024-02-01",
        "end_date": "2025-01-31",
        "rent_amount": 1500.00,
        "security_deposit": 1500.00,
        "lease_type": "fixed",     # fixed, month_to_month, weekly
        "payment_due_day": 1       # Day of month rent is due
    }
)
```

### Renew Lease

```python
property_manager_tool(
    action="renew_lease",
    lease_id=1,
    data={
        "new_end_date": "2026-01-31",
        "new_rent": 1575.00         # Optional: new rent amount
    }
)
```

### Terminate Lease

```python
property_manager_tool(
    action="terminate_lease",
    lease_id=1,
    reason="Tenant relocated for work"
)
```

### View Expiring Leases

```python
property_manager_tool(
    action="expiring_leases",
    days=30                          # Leases expiring within X days
)
```

## Rent Collection

### Record Payment

```python
property_manager_tool(
    action="record_payment",
    data={
        "lease_id": 1,
        "amount": 1500.00,
        "payment_date": "2024-02-01",
        "payment_method": "check",   # cash, check, bank_transfer, credit_card, venmo, zelle
        "reference_number": "Check #1234"
    }
)
```

### View Rent Roll

See all expected and received rent for a month:

```python
property_manager_tool(
    action="rent_roll",
    month="2024-02"                  # Optional: defaults to current month
)
```

### View Overdue Rent

```python
property_manager_tool(action="overdue_rent")
```

## Expense Tracking

### Record Expense

```python
property_manager_tool(
    action="record_expense",
    data={
        "property_id": 1,
        "unit_id": None,             # Optional: specific unit
        "category": "maintenance",
        "description": "HVAC repair",
        "amount": 450.00,
        "expense_date": "2024-02-15",
        "vendor": "ABC HVAC Services",
        "is_recurring": False
    }
)
```

Expense categories: `maintenance`, `repairs`, `utilities`, `insurance`, `taxes`, `mortgage`, `management`, `legal`, `advertising`, `supplies`, `other`

### Expense Report

```python
property_manager_tool(
    action="expense_report",
    property_id=1,
    data={
        "start_date": "2024-01-01",
        "end_date": "2024-12-31"
    }
)
```

## Maintenance Management

### Create Maintenance Request

```python
property_manager_tool(
    action="create_maintenance",
    data={
        "property_id": 1,
        "unit_id": None,             # Optional: specific unit
        "category": "plumbing",
        "title": "Leaky faucet in kitchen",
        "description": "Kitchen sink faucet drips constantly",
        "priority": "normal",        # emergency, high, normal, low
        "estimated_cost": 150.00
    }
)
```

Maintenance categories: `plumbing`, `electrical`, `hvac`, `appliance`, `structural`, `roofing`, `landscaping`, `cleaning`, `pest_control`, `general`

### Update Maintenance Status

```python
property_manager_tool(
    action="update_maintenance",
    request_id=1,
    data={
        "status": "in_progress",     # open, scheduled, in_progress, completed, cancelled
        "assigned_to": "ABC Plumbing",
        "scheduled_date": "2024-02-20"
    }
)
```

### Complete Maintenance

```python
property_manager_tool(
    action="complete_maintenance",
    request_id=1,
    data={
        "actual_cost": 175.00,
        "notes": "Replaced faucet cartridge and handles"
    }
)
```

### View Maintenance Schedule

```python
property_manager_tool(action="maintenance_schedule")
```

## Financial Reporting

### Property Financials

Get detailed financials for a property:

```python
property_manager_tool(
    action="financials",
    property_id=1,
    year=2024                        # Optional: defaults to current year
)
```

### Portfolio Financials

Get financials across all properties:

```python
property_manager_tool(
    action="financials",
    year=2024
)
```

### Cash Flow Projection

Project future cash flow for a property:

```python
property_manager_tool(
    action="cash_flow",
    property_id=1,
    months=12                        # Number of months to project
)
```

## Workflow Examples

### Setting Up a New Rental

1. **Add the property:**
   ```python
   property_manager_tool(action="add_property", data={...})
   ```

2. **Add tenant:**
   ```python
   property_manager_tool(action="add_tenant", data={...})
   ```

3. **Create lease:**
   ```python
   property_manager_tool(action="create_lease", data={...})
   ```

4. **Record first month's rent:**
   ```python
   property_manager_tool(action="record_payment", data={...})
   ```

### Monthly Rent Collection

1. **Check rent roll:**
   ```python
   property_manager_tool(action="rent_roll")
   ```

2. **Record payments as received:**
   ```python
   property_manager_tool(action="record_payment", data={...})
   ```

3. **Follow up on overdue:**
   ```python
   property_manager_tool(action="overdue_rent")
   ```

### Managing the West Bethel Motel

1. **Generate rooms:**
   ```python
   property_manager_tool(action="generate_motel_units", property_id=1, data={"count": 20, "base_rent": 89.00})
   ```

2. **Track daily occupancy:**
   ```python
   property_manager_tool(action="get_property", property_id=1)
   ```

3. **Record guest stays (short-term leases):**
   ```python
   property_manager_tool(action="create_lease", data={
       "property_id": 1,
       "unit_id": 5,
       "tenant_id": 10,
       "start_date": "2024-02-15",
       "end_date": "2024-02-17",
       "rent_amount": 178.00,
       "lease_type": "short_term"
   })
   ```

## Integration with Other Tools

- Use **diagram_tool** to visualize property portfolio and cash flow
- Use **business_xray_tool** to analyze rental business opportunities
- Generate reports for tax purposes and financial planning
