# Business X-Ray Quick Reference

## Quick Commands

### Agent Jumbo Commands

```
"Run a comprehensive business x-ray for [Company Name]"
"Analyze my business health"
"Audit my time usage this week"
"Find automation opportunities"
"Scan for revenue opportunities"
"Check my work-life balance"
```

### Python Tool Calls

```python
# Comprehensive analysis
business_xray_tool(
    analysis_type="comprehensive",
    business_name="Company Name"
)

# Business health
business_xray_tool(
    analysis_type="health",
    business_name="Company Name",
    data={"monthly_revenue": 50000, "growth_rate": 8, ...}
)

# Time audit
business_xray_tool(
    analysis_type="time",
    data={"deep_work_hours": 20, "meeting_hours": 10, ...}
)

# Automation scan
business_xray_tool(
    analysis_type="automation",
    data={"opportunities": [...], "hourly_rate": 75}
)

# Revenue scan
business_xray_tool(
    analysis_type="revenue",
    data={"current_annual_revenue": 120000, "opportunities": [...]}
)

# Balance check
business_xray_tool(
    analysis_type="balance",
    data={"work_hours_week": 55, "stress_level": 7, ...}
)
```

## Scoring Quick Reference

### Business Health (0-100)

| Score | Status | Action |
|-------|--------|--------|
| 80-100 | Excellent | Scale aggressively |
| 60-79 | Good | Optimize and grow |
| 40-59 | Needs work | Fix fundamentals |
| 0-39 | Critical | Immediate action |

**Key Metrics:**

- Revenue Growth: >10% = Excellent
- Profit Margin: >30% = Excellent
- LTV/CAC Ratio: >3x = Excellent
- Churn Rate: <5% = Excellent

### Time Efficiency (%)

| Score | Status |
|-------|--------|
| 50%+ | World-class |
| 40-50% | Excellent |
| 30-40% | Good |
| 20-30% | Below average |
| <20% | Inefficient |

**Formula:** (Deep Work Hours / Total Work Hours) × 100

### Life Balance (0-100)

| Score | Status |
|-------|--------|
| 85-100 | Optimal |
| 70-84 | Good |
| 55-69 | Needs attention |
| 40-54 | Risk of burnout |
| 0-39 | Critical |

**Components:**

- Work hours vs ideal (25 pts)
- Stress level (25 pts)
- Health metrics (25 pts)
- Life satisfaction (25 pts)

## Output Files

```
/tmp/business_xray/
├── business_xray_TIMESTAMP.json       # Full data
├── executive_summary.md               # Overview
├── dashboard.md                      # All modules
├── business_health.mmd               # Health chart
├── time_audit.mmd                    # Time pie chart
├── automation_opportunities.md       # ROI table
├── revenue_opportunities.mmd         # Revenue flow
└── life_balance.md                   # Balance chart
```

## Common Workflows

### Monthly Review

1. Run comprehensive x-ray
2. Review executive summary
3. Pick top 3 actions
4. Track in next month

### Automation Sprint

1. Run automation scan
2. Sort by annual savings
3. Pick highest ROI
4. Implement in 1 week
5. Measure time saved

### Revenue Growth

1. Scan opportunities
2. Pick 1 quick win (1-2 months)
3. Pick 1 medium win (3-6 months)
4. Execute and measure

### Balance Check

1. Run weekly balance check
2. Track trends over time
3. Adjust if score <70
4. Maintain if score >85

## Integration with Diagrams

```python
# Generate x-ray report
business_xray_tool(analysis_type="comprehensive", ...)

# Export diagrams to PNG
diagram_tool(
    diagram_type="mermaid",
    content=read_file("/tmp/business_xray/business_health.mmd"),
    format="png",
    output_file="/tmp/health.png"
)
```

## Typical Analysis Results

### Startup (Year 1)

- Health: 45-65 (building phase)
- Efficiency: 25-35% (learning)
- Automation savings: $50-100k
- Revenue opportunities: +50-100%
- Balance: 40-60 (high stress)

### Growing Business (Year 2-5)

- Health: 65-80 (scaling)
- Efficiency: 35-45% (optimizing)
- Automation savings: $100-200k
- Revenue opportunities: +25-50%
- Balance: 55-75 (improving)

### Established Business (Year 5+)

- Health: 75-90 (mature)
- Efficiency: 40-55% (optimized)
- Automation savings: $50-150k
- Revenue opportunities: +10-25%
- Balance: 70-85 (sustainable)

## Red Flags

### Business Health

- ⚠️ Growth rate <0% (declining)
- ⚠️ Profit margin <10% (unsustainable)
- ⚠️ LTV/CAC <1 (losing money per customer)
- ⚠️ Churn >20% (major retention issue)

### Time Efficiency

- ⚠️ Deep work <15h/week (not enough focus)
- ⚠️ Meetings >20h/week (meeting overload)
- ⚠️ Efficiency <20% (severe inefficiency)
- ⚠️ Context switches >30/day (fragmentation)

### Life Balance

- ⚠️ Work hours >60/week (burnout risk)
- ⚠️ Stress level >8/10 (critical stress)
- ⚠️ Sleep <6h/night (health risk)
- ⚠️ Exercise <2h/week (sedentary)
- ⚠️ Life satisfaction <4/10 (crisis)

## Quick Wins by Module

### Business Health

1. Raise prices 10-20% (quick revenue boost)
2. Reduce churn with customer success program
3. Improve CAC with referral program

### Time Efficiency

1. Block 4h focus time daily
2. Decline 30% of meetings
3. Batch email to 2x daily

### Automation

1. Automate invoicing (95% potential)
2. Set up email templates (70% potential)
3. Auto-post social media (80% potential)

### Revenue

1. Upsell existing customers (low difficulty)
2. Create premium tier (medium difficulty)
3. Launch digital product (medium difficulty)

### Balance

1. Set hard stop time (6pm no work)
2. Schedule 3 exercise sessions
3. Block family time on calendar

## Troubleshooting

**"Low health score"**
→ Focus on 1 metric at a time, run revenue scan

**"Low efficiency"**
→ Eliminate distractions, block focus time, automate routine tasks

**"Low balance score"**
→ Delegate/automate to reduce hours, set boundaries, prioritize health

**"No automation opportunities found"**
→ Review task list manually, track time for 1 week, re-run

**"Diagram not rendering"**
→ Check .mmd file syntax, verify mermaid.js loaded, try PNG export

## Best Practices

1. **Track Trends** - Save reports monthly, compare scores
2. **Set Goals** - Target +10 points per quarter
3. **Act Fast** - Implement top 3 within 30 days
4. **Measure Impact** - Re-run after changes
5. **Share Results** - Export diagrams for stakeholders
6. **Stay Consistent** - Monthly comprehensive, weekly balance
7. **Use Real Data** - Actual numbers > estimates

## Resources

- Full docs: `/docs/business_xray.md`
- Diagram docs: `/docs/diagrams.md`
- Agent prompts: `/prompts/agent.system.tool.business_xray_tool.md`
- Implementation: `/BUSINESS_XRAY_IMPLEMENTATION.md`

## Support

- GitHub Issues: Report bugs
- Discord/Skool: Ask questions
- Show & Tell: Share results

---

**Remember:** Analysis without action is procrastination. Pick your top 3, execute in 30 days, measure results.
