# Customer Lifecycle Tool

The **customer_lifecycle** tool automates the complete customer journey from lead capture through solution delivery and ongoing support.

## Purpose

Manage end-to-end customer lifecycle including:

- Lead capture and qualification
- Requirements gathering through structured interviews
- Solution architecture design
- Proposal generation and tracking
- Customer health monitoring
- Pipeline analytics

## Available Actions

### 1. capture_lead

**Capture new lead and initiate qualification process**

```
{{customer_lifecycle(
  action="capture_lead",
  name="John Smith",
  company="Acme Corp",
  email="john@acme.com",
  phone="+1-555-0123",
  industry="Healthcare",
  company_size="51-200",
  source="website_form",
  notes="Interested in cloud migration"
)}}
```

**Parameters:**

- `name` (required): Lead contact name
- `company` (optional): Company name
- `email` (optional): Contact email
- `phone` (optional): Contact phone
- `industry` (optional): Industry sector
- `company_size` (optional): Employee count range
- `source` (optional): Lead source (website, referral, event, etc.)
- `notes` (optional): Initial notes

**Returns:** Customer ID, stage, next step

---

### 2. conduct_interview

**Conduct structured requirements gathering interview**

```
{{customer_lifecycle(
  action="conduct_interview",
  customer_id=1,
  responses={
    "What business problem are you trying to solve?": "Our legacy system can't scale with growth",
    "Who are the primary users?": "Sales team (50 people) and management (10)",
    "What are your main pain points?": "Slow performance, data silos, no mobile access",
    "What does success look like?": "Real-time data access, 10x faster, mobile-first",
    "What are your timeline expectations?": "Launch in 6 months",
    "What is your budget range?": "$100k-$200k"
  }
)}}
```

**Parameters:**

- `customer_id` (required): Customer ID from lead capture
- `responses` (required): Dictionary of question/answer pairs
- `questions` (optional): Custom interview questions (uses defaults if not provided)

**Returns:** Requirement ID, structured requirements, pain points, success criteria

**Default Interview Questions:**

1. What business problem are you trying to solve?
2. Who are the primary users/stakeholders?
3. What are your main pain points with current solutions?
4. What does success look like for this project?
5. What are your timeline expectations?
6. What is your budget range?
7. Are there any specific technical constraints or preferences?
8. What integrations are required?
9. What are your scalability requirements?
10. What compliance/security requirements exist?

---

### 3. design_solution

**Design solution architecture based on requirements**

```
{{customer_lifecycle(
  action="design_solution",
  customer_id=1,
  requirement_id=1,
  solution_name="Cloud Migration Platform",
  architecture_preferences={
    "cloud_provider": "Azure",
    "scalability": "high",
    "compliance": ["HIPAA", "SOC2"]
  }
)}}
```

**Parameters:**

- `customer_id` (required): Customer ID
- `requirement_id` (optional): Specific requirement (uses latest if not provided)
- `solution_name` (optional): Solution name
- `architecture_preferences` (optional): Technical preferences

**Returns:** Solution ID, architecture design (type, tech stack, components)

---

### 4. generate_proposal

**Generate comprehensive customer proposal**

```
{{customer_lifecycle(
  action="generate_proposal",
  customer_id=1,
  solution_id=1,
  pricing_model="fixed_price",
  discount_percentage=10
)}}
```

**Parameters:**

- `customer_id` (required): Customer ID
- `solution_id` (optional): Solution ID (uses latest if not provided)
- `pricing_model` (optional): "fixed_price", "time_materials", "milestone_based" (default: "fixed_price")
- `discount_percentage` (optional): Discount percentage (default: 0)

**Returns:** Proposal ID, content, cost, timeline, deliverables

**Pricing Models:**

- `fixed_price`: Fixed total cost
- `time_materials`: Hourly/daily rates
- `milestone_based`: Payment tied to deliverables

---

### 5. track_proposal

**Track proposal status and follow-up actions**

```
{{customer_lifecycle(
  action="track_proposal",
  proposal_id=1,
  status="sent"
)}}
```

**Parameters:**

- `proposal_id` (required): Proposal ID
- `status` (optional): Update status ("draft", "sent", "accepted", "rejected")

**Returns:** Proposal status, days pending, recommended follow-up action

**Proposal Statuses:**

- `draft`: Not yet sent
- `sent`: Awaiting customer response
- `accepted`: Customer accepted (auto-promotes to "customer" stage)
- `rejected`: Customer declined

---

### 6. get_customer_view

**Get 360-degree view of customer**

```
{{customer_lifecycle(
  action="get_customer_view",
  customer_id=1
)}}
```

**Parameters:**

- `customer_id` (required): Customer ID

**Returns:** Complete customer profile including:

- Basic info (name, company, contact)
- Requirements sessions count
- Solutions designed count
- Proposals by status
- Active projects count
- Project completion percentage
- Open support tickets

---

### 7. check_customer_health

**Calculate customer health score and get recommendations**

```
{{customer_lifecycle(
  action="check_customer_health",
  customer_id=1
)}}
```

**Parameters:**

- `customer_id` (required): Customer ID

**Returns:** Health score (0-100), status, factors, recommendations

**Health Statuses:**

- `healthy` (80-100): All systems go
- `at_risk` (60-79): Needs attention
- `critical` (0-59): Urgent intervention needed

**Health Factors:**

- Support ticket volume
- Active project count
- Project completion rate
- Engagement frequency

---

### 8. get_pipeline_summary

**Get sales pipeline analytics**

```
{{customer_lifecycle(
  action="get_pipeline_summary"
)}}
```

**Returns:** Customers by stage, proposals by status, total values

**Customer Stages:**

- `lead`: Initial contact, not qualified
- `prospect`: Qualified, requirements gathered
- `customer`: Active contract/project
- `churned`: Lost customer

---

### 9. update_customer_stage

**Manually update customer lifecycle stage**

```
{{customer_lifecycle(
  action="update_customer_stage",
  customer_id=1,
  stage="customer"
)}}
```

**Parameters:**

- `customer_id` (required): Customer ID
- `stage` (required): New stage ("lead", "prospect", "customer", "churned")

**Returns:** Success status

---

### 10. list_customers

**List customers with optional filters**

```
{{customer_lifecycle(
  action="list_customers",
  stage="prospect",
  industry="Healthcare",
  limit=10
)}}
```

**Parameters:**

- `stage` (optional): Filter by stage
- `industry` (optional): Filter by industry
- `limit` (optional): Max results

**Returns:** Customer list with ID, name, company, email, stage

---

## Typical Workflow

### Lead to Customer Journey

1. **Capture Lead** → Get customer_id
2. **Conduct Interview** → Gather requirements
3. **Design Solution** → Create architecture
4. **Generate Proposal** → Build offer
5. **Track Proposal** → Monitor status
6. **Update Stage to "customer"** (when accepted)
7. **Check Health** → Ongoing monitoring

### Example Complete Flow

```
# Step 1: Capture lead
{{customer_lifecycle(action="capture_lead", name="Sarah Johnson", company="MedTech Inc", email="sarah@medtech.com", industry="Healthcare")}}
# Returns: customer_id = 5

# Step 2: Interview
{{customer_lifecycle(action="conduct_interview", customer_id=5, responses={"What business problem?": "Need HIPAA-compliant patient portal"})}}
# Returns: requirement_id = 3

# Step 3: Design solution
{{customer_lifecycle(action="design_solution", customer_id=5, requirement_id=3)}}
# Returns: solution_id = 2

# Step 4: Generate proposal
{{customer_lifecycle(action="generate_proposal", customer_id=5, solution_id=2, discount_percentage=15)}}
# Returns: proposal_id = 7

# Step 5: Track proposal
{{customer_lifecycle(action="track_proposal", proposal_id=7, status="sent")}}
# Returns: days_pending, follow_up_action

# Step 6: Check customer health (ongoing)
{{customer_lifecycle(action="check_customer_health", customer_id=5)}}
```

---

## Integration with Other Tools

### With Portfolio Manager

After proposal acceptance, create project:

```
# Customer accepted proposal
{{customer_lifecycle(action="track_proposal", proposal_id=7, status="accepted")}}

# Create project in portfolio
{{portfolio_manager_tool(action="create_project", project_name="MedTech Patient Portal", client="MedTech Inc")}}
```

### With Virtual Team

Route solution design to specialized agents:

```
# Get solution architecture
{{customer_lifecycle(action="design_solution", customer_id=5)}}

# Assign to architect for detailed design
{{virtual_team(action="create_task", task_type="architecture_design", agent_role="architect", context="Design HIPAA-compliant patient portal")}}
```

---

## Best Practices

1. **Always capture leads first** - Don't skip to interview without customer record
2. **Use structured interviews** - Default questions cover all critical areas
3. **Track proposal follow-ups** - Check days_pending and act on recommendations
4. **Monitor customer health** - Run health checks monthly for active customers
5. **Update stages properly** - Stage transitions drive automation (e.g., accepted proposal → customer)
6. **Link to projects** - Connect customer_projects to portfolio for full visibility

---

## Notes

- Database auto-creates on first use
- All timestamps in ISO format
- Proposal numbers auto-generated (PROP-{customer_id}-{count})
- Customer stage auto-updates on proposal acceptance
- Health scores recalculate on-demand (not cached)
