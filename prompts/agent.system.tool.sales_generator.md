# Sales Generator Tool

The **sales_generator** tool creates customer-facing materials including proposals, demos, ROI analyses, case studies, portfolio showcases, and business cases.

## Purpose

- Generate professional proposals with pricing
- Create demo scripts and specifications
- Calculate ROI with multi-scenario projections
- Build case studies from completed projects
- Showcase portfolio for specific industries
- Develop comprehensive business cases
- Create competitive comparisons

---

## Available Actions

### Proposals

#### 1. generate_proposal

**Generate a full proposal document**

```
{{sales_generator(
  action="generate_proposal",
  title="Website Redesign Proposal",
  customer_id=5,
  customer_name="Acme Corp",
  solution_summary="Complete website redesign with modern UI",
  items=[
    {"name": "Design Phase", "description": "UI/UX design", "quantity": 1, "unit_price": 5000},
    {"name": "Development", "description": "Frontend & backend", "quantity": 1, "unit_price": 15000},
    {"name": "Testing", "description": "QA and UAT", "quantity": 1, "unit_price": 3000}
  ],
  valid_days=30
)}}
```

**Parameters:**

- `title` (required): Proposal title
- `customer_id` (optional): Link to customer_lifecycle
- `customer_name` (optional): Customer name
- `solution_summary` (optional): Brief solution description
- `items` (optional): Array of line items with name, description, quantity, unit_price
- `valid_days` (optional): Days until expiration (default: 30)

**Returns:** proposal_id, content preview, total price

---

#### 2. get_proposal

**Get full proposal details**

```
{{sales_generator(
  action="get_proposal",
  proposal_id=1
)}}
```

---

#### 3. list_proposals

**List proposals with filters**

```
{{sales_generator(
  action="list_proposals",
  customer_id=5,
  status="draft"
)}}
```

**Parameters:**

- `customer_id` (optional): Filter by customer
- `status` (optional): Filter by status (draft, sent, accepted, declined)

---

#### 4. update_proposal_status

**Update proposal status**

```
{{sales_generator(
  action="update_proposal_status",
  proposal_id=1,
  status="sent"
)}}
```

---

### Demos

#### 5. create_demo

**Create a demo specification**

```
{{sales_generator(
  action="create_demo",
  title="Product Demo for Acme",
  customer_name="Acme Corp",
  demo_type="interactive",
  description="Showcase our platform capabilities",
  features=[
    {"name": "Dashboard", "description": "Real-time analytics", "steps": ["Login", "Navigate to dashboard", "Show metrics"]},
    {"name": "Reporting", "description": "Custom reports", "steps": ["Generate report", "Export to PDF"]},
    "User Management"
  ]
)}}
```

**Parameters:**

- `title` (required): Demo title
- `customer_id` (optional): Link to customer
- `customer_name` (optional): Customer name
- `demo_type` (optional): interactive, recorded, walkthrough
- `features` (optional): Features to demonstrate (strings or objects with steps)
- `description` (optional): Demo overview

**Returns:** demo_id, generated demo script

---

#### 6. get_demo / list_demos

**Retrieve demo details or list demos**

```
{{sales_generator(action="get_demo", demo_id=1)}}
{{sales_generator(action="list_demos", customer_id=5)}}
```

---

### ROI Analysis

#### 7. calculate_roi

**Calculate ROI with projections**

```
{{sales_generator(
  action="calculate_roi",
  title="Automation ROI Analysis",
  customer_name="Acme Corp",
  current_costs={
    "manual_processing": 50000,
    "error_correction": 15000,
    "overtime": 10000
  },
  projected_savings={
    "labor_reduction": 35000,
    "error_elimination": 12000,
    "efficiency_gains": 8000
  },
  implementation_cost=75000,
  years=3
)}}
```

**Parameters:**

- `title` (required): ROI analysis title
- `customer_id` (optional): Link to customer
- `customer_name` (optional): Customer name
- `current_costs` (optional): Dictionary of current annual costs
- `projected_savings` (optional): Dictionary of projected annual savings
- `implementation_cost` (optional): One-time implementation cost
- `years` (optional): Projection years (default: 3)

**Returns:** ROI calculation with:

- Summary (annual savings, payback period, ROI %, NPV)
- Three scenarios: Conservative (50%), Moderate (75%), Aggressive (100%)
- Year-by-year projections

---

#### 8. get_roi / list_roi

**Retrieve ROI calculation or list all**

```
{{sales_generator(action="get_roi", roi_id=1)}}
{{sales_generator(action="list_roi", customer_id=5)}}
```

---

### Case Studies

#### 9. generate_case_study

**Generate a case study from a completed project**

```
{{sales_generator(
  action="generate_case_study",
  project_name="E-Commerce Platform Migration",
  customer_name="RetailCo",
  industry="retail",
  challenge="Legacy platform couldn't handle scale during peak seasons",
  solution="Migrated to cloud-native microservices architecture",
  results="99.9% uptime during Black Friday, 3x faster page loads",
  metrics={
    "Uptime": "99.9%",
    "Page Load": "1.2s (from 3.8s)",
    "Revenue Increase": "45%"
  },
  testimonial="The migration transformed our digital presence. - CTO, RetailCo"
)}}
```

**Parameters:**

- `project_name` (required): Project name
- `customer_id` (optional): Link to customer
- `customer_name` (optional): Customer name
- `industry` (optional): Industry sector
- `challenge` (optional): The problem faced
- `solution` (optional): How we solved it
- `results` (optional): Outcomes achieved
- `metrics` (optional): Dictionary of key metrics
- `testimonial` (optional): Customer quote

**Returns:** case_study_id, formatted case study content

---

#### 10. get_case_study / list_case_studies

```
{{sales_generator(action="get_case_study", case_study_id=1)}}
{{sales_generator(action="list_case_studies", industry="healthcare")}}
```

---

### Portfolio Showcases

#### 11. generate_portfolio_showcase

**Generate a portfolio presentation**

```
{{sales_generator(
  action="generate_portfolio_showcase",
  title="Healthcare Solutions Portfolio",
  description="Our track record in healthcare digital transformation",
  target_industry="healthcare",
  projects=[
    {
      "name": "Patient Portal",
      "description": "Self-service portal for appointments and records",
      "tech_stack": ["React", "Node.js", "PostgreSQL"],
      "outcomes": "50% reduction in call center volume"
    },
    {
      "name": "Telemedicine Platform",
      "description": "HIPAA-compliant video consultations",
      "tech_stack": ["Vue.js", "Python", "WebRTC"],
      "outcomes": "10,000+ consultations monthly"
    }
  ]
)}}
```

**Parameters:**

- `title` (required): Showcase title
- `description` (optional): Overview text
- `projects` (optional): Array of projects to feature
- `target_industry` (optional): Industry focus

**Returns:** showcase_id, formatted showcase content

---

#### 12. get_showcase / list_showcases

```
{{sales_generator(action="get_showcase", showcase_id=1)}}
{{sales_generator(action="list_showcases", target_industry="fintech")}}
```

---

### Business Cases

#### 13. build_business_case

**Build a comprehensive business case**

```
{{sales_generator(
  action="build_business_case",
  title="Digital Transformation Initiative",
  customer_name="Acme Corp",
  problem_statement="Manual processes causing delays and errors",
  proposed_solution="Implement integrated workflow automation",
  benefits=[
    "50% reduction in processing time",
    "90% error reduction",
    "Improved compliance tracking"
  ],
  risks=[
    "Change management challenges",
    "Integration complexity",
    "Training requirements"
  ],
  timeline="6 months implementation",
  investment_required=150000,
  recommendation="Proceed with Phase 1 pilot"
)}}
```

**Parameters:**

- `title` (required): Business case title
- `customer_id` (optional): Link to customer
- `customer_name` (optional): Customer name
- `problem_statement` (optional): The challenge being addressed
- `proposed_solution` (optional): Recommended approach
- `benefits` (optional): List of expected benefits
- `risks` (optional): List of identified risks
- `timeline` (optional): Implementation timeline
- `investment_required` (optional): Total investment amount
- `recommendation` (optional): Final recommendation

**Returns:** case_id, executive summary

---

#### 14. get_business_case / list_business_cases

```
{{sales_generator(action="get_business_case", case_id=1)}}
{{sales_generator(action="list_business_cases", customer_id=5)}}
```

---

### Competitive Comparisons

#### 15. create_comparison

**Create competitive comparison**

```
{{sales_generator(
  action="create_comparison",
  title="CRM Platform Comparison",
  our_solution="Our CRM Platform",
  competitors=["Salesforce", "HubSpot", "Zoho"],
  criteria=[
    {"name": "Pricing", "our_score": "Competitive"},
    {"name": "Customization", "our_score": "Excellent"},
    {"name": "Integration", "our_score": "Strong"},
    {"name": "Support", "our_score": "24/7 dedicated"}
  ]
)}}
```

**Parameters:**

- `title` (required): Comparison title
- `our_solution` (required): Our solution name
- `competitors` (optional): List of competitor names
- `criteria` (optional): List of comparison criteria

**Returns:** comparison_id, comparison analysis

---

#### 16. get_comparison / list_comparisons

```
{{sales_generator(action="get_comparison", comparison_id=1)}}
{{sales_generator(action="list_comparisons")}}
```

---

### Statistics

#### 17. get_stats

**Get overall statistics**

```
{{sales_generator(action="get_stats")}}
```

**Returns:** Totals for all material types, proposal status breakdown

---

## Typical Workflows

### Complete Sales Cycle

```
# 1. Get customer requirements from customer_lifecycle
{{customer_lifecycle(action="get_customer_view", customer_id=5)}}

# 2. Calculate ROI based on their situation
{{sales_generator(
  action="calculate_roi",
  title="Automation ROI",
  customer_id=5,
  current_costs={"manual_work": 80000},
  projected_savings={"automation": 50000}
)}}

# 3. Generate proposal
{{sales_generator(
  action="generate_proposal",
  title="Automation Solution",
  customer_id=5,
  items=[...],
  solution_summary="..."
)}}

# 4. Create demo for presentation
{{sales_generator(
  action="create_demo",
  title="Solution Demo",
  customer_id=5,
  features=[...]
)}}

# 5. Track proposal status
{{sales_generator(
  action="update_proposal_status",
  proposal_id=1,
  status="sent"
)}}
```

### Industry-Focused Showcase

```
# 1. Pull relevant case studies
{{sales_generator(action="list_case_studies", industry="healthcare")}}

# 2. Get portfolio projects
{{portfolio_manager_tool(action="list", tech="React")}}

# 3. Create targeted showcase
{{sales_generator(
  action="generate_portfolio_showcase",
  title="Healthcare Solutions",
  target_industry="healthcare",
  projects=[...]
)}}
```

---

## Integration with Other Tools

### With Customer Lifecycle

Link all materials to customer records:

```
{{sales_generator(action="generate_proposal", customer_id=5, ...)}}
```

### With Portfolio Manager

Pull project data for showcases:

```
{{portfolio_manager_tool(action="list")}}
{{sales_generator(action="generate_portfolio_showcase", projects=[...])}}
```

### With Business X-Ray

Use analysis for ROI calculations:

```
{{business_xray_tool(action="get_analysis", customer_id=5)}}
{{sales_generator(action="calculate_roi", ...)}}
```

### With Diagram Architect

Include architecture visuals in proposals:

```
{{diagram_architect(action="generate_system_diagram", analysis_id=1)}}
# Reference diagram in proposal content
```

---

## Notes

- All materials stored in SQLite for tracking
- Proposals include automatic expiration dates
- ROI calculations support three scenarios
- Case studies can be filtered by industry
- Showcases can be targeted to specific industries
- All content generated in Markdown format
