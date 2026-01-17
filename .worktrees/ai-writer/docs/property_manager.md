# Property Manager

The Property Manager is a comprehensive rental property management tool for residential and commercial properties. It handles tenants, leases, rent collection, maintenance, expenses, and financial reporting.

## Your Properties

The system is pre-configured for:
- **West Bethel Motel** - Commercial/Motel in Bethel, ME
- **3 Houses** - Residential properties (update addresses as needed)

## Features

- **Property Tracking**: Manage multiple properties with units
- **Tenant Management**: Full tenant profiles and history
- **Lease Management**: Create, renew, and terminate leases
- **Rent Collection**: Track payments, view rent roll, identify overdue
- **Maintenance**: Request tracking from open to completed
- **Expense Tracking**: Categorize and report on all expenses
- **Financial Reports**: Income, expenses, ROI, cash flow projections

## Quick Start

### 1. Initialize Properties

Set up your initial properties:

```
Initialize my property portfolio
```

### 2. View Dashboard

Get an overview of your portfolio:

```
Show me my property management dashboard
```

### 3. Add a Tenant

```
Add tenant John Smith with email john@email.com and phone 207-555-1234
```

### 4. Create a Lease

```
Create a lease for tenant 1 at property 1 starting 2024-02-01 at $1500/month
```

### 5. Record Rent Payment

```
Record rent payment of $1500 for lease 1
```

## Database Location

Property data is stored at `/a0/data/properties.db` (persisted across container restarts).

## Property Types

- `house` - Single-family home
- `apartment` - Apartment unit
- `condo` - Condominium
- `townhouse` - Townhouse
- `duplex` - Duplex property
- `motel` - Motel (multi-unit, short-term)
- `commercial` - Commercial property
- `mixed_use` - Mixed residential/commercial

## Actions Reference

### Overview
| Action | Description |
|--------|-------------|
| `dashboard` | Complete portfolio overview |
| `portfolio_summary` | Financial summary |
| `financials` | Detailed financial report |
| `setup_initial` | Initialize your properties |

### Properties
| Action | Description |
|--------|-------------|
| `list_properties` | List all properties |
| `get_property` | Get property details |
| `add_property` | Add new property |
| `update_property` | Update property info |

### Units
| Action | Description |
|--------|-------------|
| `add_units` | Add units to property |
| `generate_motel_units` | Auto-generate motel rooms |

### Tenants
| Action | Description |
|--------|-------------|
| `add_tenant` | Add new tenant |
| `search_tenants` | Search tenants |
| `tenant_history` | View tenant history |

### Leases
| Action | Description |
|--------|-------------|
| `create_lease` | Create new lease |
| `renew_lease` | Renew existing lease |
| `terminate_lease` | Terminate lease |
| `expiring_leases` | View expiring leases |

### Rent
| Action | Description |
|--------|-------------|
| `record_payment` | Record rent payment |
| `rent_roll` | View rent roll |
| `overdue_rent` | View overdue payments |

### Expenses
| Action | Description |
|--------|-------------|
| `record_expense` | Record expense |
| `expense_report` | View expense report |

### Maintenance
| Action | Description |
|--------|-------------|
| `create_maintenance` | Create request |
| `update_maintenance` | Update status |
| `complete_maintenance` | Complete request |
| `maintenance_schedule` | View schedule |

### Financial
| Action | Description |
|--------|-------------|
| `cash_flow` | Cash flow projection |

## West Bethel Motel Management

For the motel, use short-term lease management:

### Generate Rooms
```
Generate 20 motel rooms at $89/night for property 1
```

### Check-In Guest
```
Create short-term lease for property 1, unit 5, guest John Doe from 2024-02-15 to 2024-02-17 at $178
```

### Check Occupancy
```
Show property 1 details
```

## Maintenance Priority Levels

- 🚨 `emergency` - Immediate attention (water leak, no heat)
- ⚠️ `high` - Within 24 hours
- 📋 `normal` - Within 1 week
- 📝 `low` - When convenient

## Expense Categories

- `maintenance` - Routine maintenance
- `repairs` - Repairs and fixes
- `utilities` - Water, electric, gas
- `insurance` - Property insurance
- `taxes` - Property taxes
- `mortgage` - Mortgage payments
- `management` - Property management fees
- `legal` - Legal fees
- `advertising` - Marketing/advertising
- `supplies` - Supplies and materials
- `other` - Other expenses

## Monthly Workflow

1. **Beginning of Month**
   - Check rent roll: `Show rent roll for 2024-02`
   - Review expiring leases: `Show leases expiring in 30 days`

2. **Throughout Month**
   - Record payments as received
   - Handle maintenance requests
   - Track expenses

3. **End of Month**
   - Check overdue rent: `Show overdue rent`
   - Review financials: `Show financials for property 1`
   - Run dashboard: `Show property dashboard`

## Integration

Works with:
- **Diagram Tool**: Visualize property portfolio and cash flow
- **Business X-Ray**: Analyze rental business opportunities
