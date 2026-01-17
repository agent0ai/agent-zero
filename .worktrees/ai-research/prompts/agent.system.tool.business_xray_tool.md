# Business X-Ray Tool

A comprehensive business analysis and life optimization tool that helps identify opportunities for automation, revenue growth, time optimization, and work-life balance improvements.

## Purpose

The Business X-Ray tool performs deep analysis across multiple dimensions of your business and personal life, generating actionable insights with visual diagrams. It integrates with the diagram tool to create compelling visualizations of all findings.

## Usage

### Comprehensive Analysis

Run a complete business x-ray covering all modules:

```python
business_xray_tool(
    analysis_type="comprehensive",
    business_name="Acme Corp",
    output_dir="/tmp/xray_reports"
)
```

This generates:
- Business health score with revenue, profitability, customer metrics
- Time usage audit with efficiency analysis
- Automation opportunities with ROI calculations
- Revenue growth opportunities
- Work-life balance assessment
- Executive summary with key recommendations

### Business Health Analysis

Analyze current business health metrics:

```python
business_xray_tool(
    analysis_type="health",
    business_name="Acme Corp",
    data={
        "monthly_revenue": 50000,
        "growth_rate": 8,
        "profit_margin": 25,
        "total_customers": 250,
        "cac": 200,
        "ltv": 2400
    }
)
```

Generates:
- Health score (0-100) based on key metrics
- Mermaid flowchart showing revenue, profitability, customer economics
- Specific recommendations for improvement

### Time Audit

Analyze how time is being spent:

```python
business_xray_tool(
    analysis_type="time",
    business_name="Acme Corp",
    data={
        "deep_work_hours": 20,
        "meeting_hours": 12,
        "email_hours": 8,
        "shallow_work_hours": 10,
        "personal_hours": 20
    }
)
```

Generates:
- Time efficiency score
- Pie chart showing time distribution
- Recommendations for optimizing focus time
- Context switching analysis

### Automation Opportunities

Identify tasks that should be automated:

```python
business_xray_tool(
    analysis_type="automation",
    business_name="Acme Corp",
    data={
        "opportunities": [
            {"task": "Invoice generation", "hours_week": 8, "potential": 95},
            {"task": "Social media posting", "hours_week": 5, "potential": 80},
            {"task": "Email responses", "hours_week": 6, "potential": 70},
            {"task": "Data entry", "hours_week": 4, "potential": 90}
        ],
        "hourly_rate": 75
    }
)
```

Generates:
- Prioritized list of automation opportunities
- Annual savings calculations
- ROI analysis
- Implementation effort estimates
- Quick wins identification

### Revenue Opportunities

Scan for revenue growth potential:

```python
business_xray_tool(
    analysis_type="revenue",
    business_name="Acme Corp",
    data={
        "current_annual_revenue": 120000,
        "opportunities": [
            {"name": "Price increase", "potential": 15000, "difficulty": 3, "months": 1},
            {"name": "Upsell program", "potential": 30000, "difficulty": 5, "months": 3},
            {"name": "New market", "potential": 50000, "difficulty": 8, "months": 6}
        ]
    }
)
```

Generates:
- Revenue opportunity flowchart
- Prioritized opportunity matrix
- Implementation timeline
- Difficulty vs. impact analysis

### Life Balance Analysis

Assess work-life balance:

```python
business_xray_tool(
    analysis_type="balance",
    business_name="Acme Corp",
    data={
        "work_hours_week": 55,
        "ideal_hours_week": 40,
        "stress_level": 7,
        "exercise_hours_week": 2,
        "sleep_hours_night": 6,
        "family_time_hours_week": 12,
        "life_satisfaction": 6
    }
)
```

Generates:
- Balance score (0-100)
- Multi-dimensional balance diagram
- Specific recommendations for improvement
- Health and wellness insights

## Integration with Diagram Tool

The Business X-Ray tool automatically generates Mermaid diagrams for all visualizations. You can further enhance these by:

1. **Exporting diagrams to images**: Use the diagram_tool to export .mmd files to PNG/SVG
2. **Customizing diagrams**: Edit generated .mmd files and re-render
3. **Creating presentations**: Combine multiple diagram outputs

Example workflow:

```python
# Step 1: Run business analysis
business_xray_tool(
    analysis_type="comprehensive",
    business_name="Acme Corp"
)

# Step 2: Export key diagrams to images for presentations
diagram_tool(
    diagram_type="mermaid",
    content=files.read_file("/tmp/business_xray/business_health.mmd"),
    format="png",
    output_file="/tmp/health_dashboard.png"
)

diagram_tool(
    diagram_type="mermaid",
    content=files.read_file("/tmp/business_xray/revenue_opportunities.mmd"),
    format="png",
    output_file="/tmp/revenue_roadmap.png"
)
```

## Common Use Cases

### 1. Monthly Business Review

```python
# Generate comprehensive monthly report
business_xray_tool(
    analysis_type="comprehensive",
    business_name="My Startup",
    output_dir=f"/reports/{current_month}"
)

# Review executive summary
files.read_file(f"/reports/{current_month}/executive_summary.md")
```

### 2. Quarterly Planning

```python
# Identify top opportunities
business_xray_tool(analysis_type="revenue", business_name="My Startup")
business_xray_tool(analysis_type="automation", business_name="My Startup")

# Create action plan based on findings
```

### 3. Work-Life Optimization

```python
# Weekly balance check
business_xray_tool(
    analysis_type="balance",
    business_name="Personal",
    data={"work_hours_week": current_hours, ...}
)

# Monthly time audit
business_xray_tool(
    analysis_type="time",
    business_name="Personal",
    data={"deep_work_hours": tracked_hours, ...}
)
```

### 4. Investor Reporting

```python
# Generate health metrics for investors
business_xray_tool(
    analysis_type="health",
    business_name="Acme Corp",
    data={
        "monthly_revenue": mrr,
        "growth_rate": mom_growth,
        "profit_margin": margin,
        "total_customers": customer_count,
        "cac": customer_acq_cost,
        "ltv": lifetime_value
    }
)

# Export diagrams for pitch deck
```

## Output Files

All analyses generate these outputs in the specified output_dir:

- `executive_summary.md` - High-level overview with key metrics
- `dashboard.md` - Visual dashboard with Mermaid diagram
- `business_health.mmd` - Health metrics flowchart
- `time_audit.mmd` - Time distribution pie chart
- `automation_opportunities.md` - Prioritized automation table
- `revenue_opportunities.mmd` - Revenue growth flowchart
- `life_balance.md` - Balance assessment with recommendations
- `business_xray_TIMESTAMP.json` - Complete data export

## Scoring System

### Business Health Score (0-100)

- **Revenue Growth** (30 points): >10% = 30pts, 5-10% = 20pts, 0-5% = 10pts
- **Profit Margin** (25 points): >30% = 25pts, 20-30% = 20pts, 10-20% = 15pts
- **LTV/CAC Ratio** (25 points): >3x = 25pts, 2-3x = 20pts, 1-2x = 10pts
- **Churn Rate** (20 points): <5% = 20pts, 5-10% = 15pts, 10-15% = 10pts

### Time Efficiency Score

Percentage of time spent on deep work vs total work time:
- **40%+**: Excellent
- **30-40%**: Good
- **20-30%**: Needs improvement
- **<20%**: Critical

### Life Balance Score (0-100)

- **Work Hours Balance** (25 points): Within 5h of ideal = 25pts
- **Stress Level** (25 points): ≤3 = 25pts, 4-5 = 15pts, 6-7 = 5pts
- **Health Metrics** (25 points): Exercise + Sleep + Satisfaction
- **Life Satisfaction** (25 points): ≥8 = 25pts, 6-7 = 15pts, 4-5 = 5pts

## Best Practices

1. **Regular Cadence**: Run comprehensive analysis monthly, specific modules weekly
2. **Track Trends**: Save reports with timestamps to see progress over time
3. **Act on Insights**: Focus on top 3 recommendations from each analysis
4. **Data Accuracy**: Use actual metrics rather than estimates when possible
5. **Combine Modules**: Use automation + revenue analysis together for maximum impact
6. **Share Visualizations**: Export diagrams to share with team/stakeholders
7. **Set Baselines**: Run initial comprehensive analysis to establish benchmarks

## Example: Complete Workflow

```python
# 1. Initial comprehensive baseline
business_xray_tool(
    analysis_type="comprehensive",
    business_name="Acme Corp",
    output_dir="/baseline/jan_2024"
)

# 2. Identify quick wins from automation
automation_results = business_xray_tool(
    analysis_type="automation",
    business_name="Acme Corp"
)

# 3. Implement top 3 automations
# ... implementation steps ...

# 4. Re-run time audit after 30 days
business_xray_tool(
    analysis_type="time",
    business_name="Acme Corp",
    output_dir="/followup/feb_2024"
)

# 5. Compare baseline vs current
# ... analyze improvements ...

# 6. Export success story diagrams
diagram_tool(
    diagram_type="mermaid",
    content="graph showing before/after time savings",
    format="png"
)
```

## Tips for Agents

- Always specify `business_name` to personalize reports
- Use `output_dir` to organize reports by date/project
- Provide actual data in `data` parameter when available
- Chain Business X-Ray with diagram_tool for presentation-ready outputs
- Read generated markdown files to provide detailed recommendations
- For recurring analysis, create templates with typical data structure
- Combine health + balance analysis for holistic view
- Use JSON output for programmatic processing
- Export key diagrams to PNG for easy sharing

## Limitations

- Comprehensive analysis requires interactive input (use specific modules for automation)
- Scoring is relative and based on general business benchmarks
- Revenue/automation opportunities require domain knowledge to validate
- Balance analysis is subjective and based on self-reported data
- Does not replace professional business consulting or financial advice

## Future Enhancements

Planned modules (not yet implemented):
- Customer journey mapping with touchpoint analysis
- Competitive intelligence gathering
- Financial health scanner with cash flow projections
- Productivity optimizer with AI recommendations
- Goal achievement tracker with milestone visualization
