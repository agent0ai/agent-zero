### portfolio_manager_tool

comprehensive code project portfolio management for organizing, analyzing, and selling software projects
scan folders to catalog projects, analyze sale-readiness, create product listings with pricing tiers, manage sales pipeline
use "action" arg: "scan" "list" "get" "add" "update" "analyze" "export" "search" "pipeline" "dashboard" "create_product" "pricing"
returns structured JSON with operation results

## Usage

### Scan Projects Folder

Scan a directory to discover and catalog projects:

```python
portfolio_manager_tool(
    action="scan",
    folder_path="/path/to/projects"
)
```

This will:

- Detect all projects in the folder
- Identify programming languages (Python, JavaScript, TypeScript, Go, Rust, Java, etc.)
- Analyze README quality, test coverage, documentation
- Calculate a sale-readiness score (0-100%)
- Add projects to the portfolio database

### List All Projects

View all projects in your portfolio:

```python
portfolio_manager_tool(
    action="list",
    filters={
        "language": "python",          # Optional: filter by language
        "status": "production",         # Optional: draft, development, production, archived
        "min_sale_readiness": 60        # Optional: minimum sale-readiness score
    }
)
```

### Get Project Details

View detailed information about a specific project:

```python
portfolio_manager_tool(
    action="get",
    project_id=1
)
```

### Analyze Project Quality

Get detailed quality analysis and recommendations:

```python
portfolio_manager_tool(
    action="analyze",
    folder_path="/path/to/project"
)
```

This provides:

- README quality score
- Test coverage percentage
- Documentation quality
- License status
- CI/CD configuration
- Specific recommendations for improvement

### Add Project Manually

Add a project that wasn't auto-detected:

```python
portfolio_manager_tool(
    action="add",
    data={
        "name": "My Project",
        "path": "/path/to/project",
        "language": "python",
        "description": "A useful tool for...",
        "status": "production",
        "tags": "ai,automation,cli"
    }
)
```

### Update Project

Update project information:

```python
portfolio_manager_tool(
    action="update",
    project_id=1,
    data={
        "status": "production",
        "description": "Updated description",
        "sale_readiness": 85
    }
)
```

### Create Product from Project

Convert a project into a sellable product:

```python
portfolio_manager_tool(
    action="create_product",
    project_id=1
)
```

### Manage Pricing Tiers

Add pricing tiers to a product:

```python
portfolio_manager_tool(
    action="pricing",
    product_id=1,
    data={
        "pricing_action": "add",
        "name": "Professional",
        "price": 299.00,
        "description": "Full source code with 1 year support",
        "features": ["Source code", "Documentation", "Email support"]
    }
)
```

List pricing tiers:

```python
portfolio_manager_tool(
    action="pricing",
    product_id=1,
    data={"pricing_action": "list"}
)
```

### Sales Pipeline Management

View your sales pipeline:

```python
portfolio_manager_tool(
    action="pipeline",
    data={"pipeline_action": "list"}
)
```

Add a lead to the pipeline:

```python
portfolio_manager_tool(
    action="pipeline",
    data={
        "pipeline_action": "add",
        "product_id": 1,
        "customer_name": "Acme Corp",
        "customer_email": "buyer@acme.com",
        "deal_value": 2999.00,
        "stage": "lead"
    }
)
```

Update pipeline stage:

```python
portfolio_manager_tool(
    action="pipeline",
    data={
        "pipeline_action": "update",
        "sale_id": 1,
        "stage": "proposal",
        "notes": "Sent pricing proposal on 2024-01-15"
    }
)
```

Pipeline stages:

- `lead` - Initial contact
- `qualified` - Confirmed interest and budget
- `proposal` - Sent pricing/proposal
- `negotiation` - Discussing terms
- `closed_won` - Sale completed
- `closed_lost` - Deal lost

### Export Product Catalog

Export your product catalog for marketing:

```python
portfolio_manager_tool(
    action="export",
    output_dir="/path/to/exports",
    format="markdown"  # or "json"
)
```

### Portfolio Dashboard

Get a high-level overview of your portfolio:

```python
portfolio_manager_tool(
    action="dashboard"
)
```

Shows:

- Total projects and products
- Average sale-readiness score
- Projects by status and language
- Pipeline value
- Top sale-ready projects

### Search Projects

Search for projects by name or description:

```python
portfolio_manager_tool(
    action="search",
    query="automation"
)
```

## Sale Readiness Score

The sale-readiness score (0-100%) is calculated based on:

| Factor | Weight | Criteria |
|--------|--------|----------|
| README Quality | 25% | Completeness, sections, clarity |
| Test Coverage | 20% | Presence of tests, coverage percentage |
| Documentation | 20% | API docs, examples, guides |
| License | 15% | Proper open-source or commercial license |
| CI/CD | 10% | Automated builds and testing |
| Code Quality | 10% | Linting, formatting, best practices |

**Score Interpretation:**

- 🟢 70-100%: Ready for sale
- 🟡 40-69%: Needs some improvement
- 🔴 0-39%: Significant work needed

## Workflow Example

1. **Scan your projects folder:**

   ```python
   portfolio_manager_tool(action="scan", folder_path="~/projects")
   ```

2. **Review and improve low-scoring projects:**

   ```python
   portfolio_manager_tool(action="analyze", folder_path="~/projects/my-tool")
   ```

3. **Create products from ready projects:**

   ```python
   portfolio_manager_tool(action="create_product", project_id=1)
   ```

4. **Add pricing tiers:**

   ```python
   portfolio_manager_tool(action="pricing", product_id=1, data={
       "pricing_action": "add",
       "name": "Basic",
       "price": 49.00
   })
   ```

5. **Track sales opportunities:**

   ```python
   portfolio_manager_tool(action="pipeline", data={
       "pipeline_action": "add",
       "product_id": 1,
       "customer_name": "Client Corp",
       "deal_value": 499.00
   })
   ```

6. **Monitor your portfolio:**

   ```python
   portfolio_manager_tool(action="dashboard")
   ```

## Integration with Other Tools

- Use **diagram_tool** to visualize your portfolio structure
- Use **business_xray_tool** to analyze revenue opportunities from your products
- Export catalogs for website or marketplace listings
