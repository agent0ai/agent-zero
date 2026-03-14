# Testing Guide - Portfolio & Property Manager

## Overview

This guide provides manual testing procedures for the newly implemented Portfolio Manager and Property Manager tools in Agent Jumbo.

## Prerequisites

- Docker containers running (`docker-compose up -d`)
- Agent Jumbo UI accessible
- Access to terminal for database verification

## Test Suite

### 1. Database Verification

Verify databases are created and accessible:

```bash
# Check data directory
ls -la /a0/data/

# Should see:
# - portfolio.db (after first use)
# - properties.db (after first use)
```

### 2. Portfolio Manager Tests

#### Test 2.1: Scan Projects Folder

**User Input:**

```
Scan my projects folder at ~/projects for portfolio
```

**Expected Result:**

- List of discovered projects
- Language detection for each project
- Sale-readiness scores (0-100%)
- Indicators for README, tests, license

**Verification:**

```bash
sqlite3 /a0/data/portfolio.db "SELECT name, language, sale_readiness FROM projects;"
```

#### Test 2.2: View Portfolio Dashboard

**User Input:**

```
Show me my portfolio dashboard
```

**Expected Result:**

- Total projects count
- Total products count
- Average sale-readiness score
- Breakdown by status and language
- Top sale-ready projects list

#### Test 2.3: Analyze Project Quality

**User Input:**

```
Analyze project at ~/projects/my-tool for sale readiness
```

**Expected Result:**

- Detailed quality breakdown table
- Scores for README, tests, license, docs, CI/CD
- Specific recommendations for improvement

#### Test 2.4: Create Product from Project

**User Input:**

```
Create a product from project ID 1
```

**Expected Result:**

- Product created confirmation
- Product ID assigned
- Base price suggested

**Verification:**

```bash
sqlite3 /a0/data/portfolio.db "SELECT id, name, base_price FROM products;"
```

#### Test 2.5: Manage Sales Pipeline

**User Input:**

```
Add Acme Corp as a lead for product 1 with deal value $499
```

**Expected Result:**

- Pipeline entry created
- Sale ID assigned
- Stage set to "lead"

**View Pipeline:**

```
Show my sales pipeline
```

### 3. Property Manager Tests

#### Test 3.1: Initialize Properties

**User Input:**

```
Initialize my property portfolio
```

**Expected Result:**

- West Bethel Motel created
- 10 motel rooms generated at $89/night
- 3 placeholder houses created
- Instructions to update house details

**Verification:**

```bash
sqlite3 /a0/data/properties.db "SELECT id, name, property_type, city FROM properties;"
sqlite3 /a0/data/properties.db "SELECT COUNT(*) FROM units WHERE property_id=1;"
```

#### Test 3.2: View Property Dashboard

**User Input:**

```
Show me my property management dashboard
```

**Expected Result:**

- Total properties count
- Total units count
- Occupancy rate
- Monthly rent income
- Alerts section (expiring leases, overdue rent, maintenance)

#### Test 3.3: Add Tenant

**User Input:**

```
Add tenant John Smith with email john@email.com and phone 207-555-1234
```

**Expected Result:**

- Tenant created confirmation
- Tenant ID assigned

**Verification:**

```bash
sqlite3 /a0/data/properties.db "SELECT id, first_name, last_name, email FROM tenants;"
```

#### Test 3.4: Create Lease

**User Input:**

```
Create a lease for tenant 1 at property 1 unit 5 starting 2026-02-01 at $89/night
```

**Expected Result:**

- Lease created confirmation
- Unit status updated to "occupied"
- Rent amount confirmed

**Verification:**

```bash
sqlite3 /a0/data/properties.db "SELECT id, tenant_id, property_id, unit_id, rent_amount, start_date FROM leases;"
sqlite3 /a0/data/properties.db "SELECT unit_number, status FROM units WHERE id=5;"
```

#### Test 3.5: Record Rent Payment

**User Input:**

```
Record rent payment of $89 for lease 1
```

**Expected Result:**

- Payment recorded confirmation
- Amount confirmed

**View Rent Roll:**

```
Show rent roll for 2026-02
```

#### Test 3.6: Create Maintenance Request

**User Input:**

```
Create maintenance request for property 1 unit 5 - leaky faucet - priority normal
```

**Expected Result:**

- Maintenance request created
- Request ID assigned
- Priority confirmed

**View Maintenance:**

```
Show maintenance schedule
```

#### Test 3.7: Record Expense

**User Input:**

```
Record expense for property 1 - maintenance - HVAC repair - $450
```

**Expected Result:**

- Expense recorded
- Amount and category confirmed

**View Expenses:**

```
Show expense report for property 1
```

#### Test 3.8: View Financials

**User Input:**

```
Show financials for property 1 for 2026
```

**Expected Result:**

- Income section (rent collected)
- Expenses by category
- Net income
- ROI percentage

### 4. Integration Tests

#### Test 4.1: Portfolio with Diagrams

**User Input:**

```
Create a diagram showing my portfolio structure
```

**Expected Result:**

- Diagram generated using diagram_tool
- Shows projects, products, pipeline

#### Test 4.2: Property Cash Flow Diagram

**User Input:**

```
Show cash flow projection for property 1 for next 12 months
```

**Expected Result:**

- Table with monthly projections
- Income, expenses, net for each month

### 5. Ollama Persistence Test

#### Test 5.1: Verify Model Persistence

**Terminal Commands:**

```bash
# Stop containers
cd /home/webemo-aaron/projects/agent-jumbo/docker/run
docker-compose down

# Restart containers
docker-compose up -d

# Check if Qwen model is still available (no re-download)
docker-compose exec agent-jumbo ollama list
```

**Expected Result:**

- `qwen2.5-coder:7b` appears in list
- No download progress (model persisted)

## Database Schema Verification

### Portfolio Database

```bash
sqlite3 /a0/data/portfolio.db ".schema"
```

Expected tables:

- projects
- products
- pricing_tiers
- sales_pipeline
- documentation

### Properties Database

```bash
sqlite3 /a0/data/properties.db ".schema"
```

Expected tables:

- properties
- units
- tenants
- leases
- rent_payments
- maintenance_requests
- expenses
- documents

## Error Scenarios to Test

### 1. Invalid Input Handling

**Test:** Try to create lease without required fields

```
Create a lease for tenant 1
```

**Expected:** Error message listing required fields

### 2. Non-existent Entity

**Test:** Try to get non-existent project

```
Show me project 9999
```

**Expected:** "Project 9999 not found" message

### 3. Empty Results

**Test:** Search for non-existent tenant

```
Search for tenant ZZZ999
```

**Expected:** "No tenants found matching 'ZZZ999'" message

## Performance Tests

### Large Folder Scan

**Test:** Scan a folder with 50+ projects

```
Scan ~/all-projects for portfolio
```

**Monitor:**

- Response time
- Memory usage
- Number of projects detected

## Cleanup

After testing, clean up test data:

```bash
# Remove test databases
rm /tmp/test_portfolio.db
rm /tmp/test_properties.db

# Optionally reset production databases (BE CAREFUL!)
# rm /a0/data/portfolio.db
# rm /a0/data/properties.db
```

## Known Limitations

1. **Portfolio Manager:**
   - Language detection based on file extensions only
   - Test coverage calculation requires pytest/jest config files
   - No GitHub integration yet

2. **Property Manager:**
   - No automatic late fee calculation
   - No integration with payment processors
   - No tenant screening/credit check features

## Troubleshooting

### Import Errors

If you see import errors:

```bash
# Verify __init__.py files exist
ls -la /home/webemo-aaron/projects/agent-jumbo/instruments/custom/portfolio_manager/__init__.py
ls -la /home/webemo-aaron/projects/agent-jumbo/instruments/custom/property_manager/__init__.py

# Check Python path
docker-compose exec agent-jumbo python3 -c "import sys; print('\n'.join(sys.path))"
```

### Database Locked

If database is locked:

```bash
# Check for active connections
lsof /a0/data/portfolio.db
lsof /a0/data/properties.db

# Restart containers
docker-compose restart
```

### Tool Not Found

If Agent Jumbo says tool not found:

```bash
# Verify tool files exist
ls -la /home/webemo-aaron/projects/agent-jumbo/python/tools/portfolio_manager_tool.py
ls -la /home/webemo-aaron/projects/agent-jumbo/python/tools/property_manager_tool.py

# Check prompts are loaded
ls -la /home/webemo-aaron/projects/agent-jumbo/prompts/agent.system.tool.portfolio_manager_tool.md
ls -la /home/webemo-aaron/projects/agent-jumbo/prompts/agent.system.tool.property_manager_tool.md
```

## Test Report Template

Use this template to document test results:

```
## Test Report - [Date]

### Environment
- Docker Version:
- Agent Jumbo Version:
- Database Versions: SQLite [version]

### Test Results

| Test ID | Test Name | Status | Notes |
|---------|-----------|--------|-------|
| 2.1 | Scan Projects | ✅ PASS | Found 5 projects |
| 2.2 | Dashboard | ✅ PASS | Rendered correctly |
| 3.1 | Initialize Props | ✅ PASS | Motel + 3 houses |
| ... | ... | ... | ... |

### Issues Found
1. [Issue description]
   - Steps to reproduce
   - Expected vs actual
   - Severity

### Recommendations
- [Improvement suggestions]
```

## Next Steps After Testing

1. Update house addresses with actual data
2. Import real project folders
3. Set up actual tenants and leases
4. Configure recurring expenses (mortgage, insurance)
5. Generate first monthly reports
