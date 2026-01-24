---
description: Calculate ROI for automation implementations
argument-hint: [automation-name] [--hourly-rate <amount>] [--list-all] [--compare]
model: claude-sonnet-4-5-20250929
allowed-tools: [Read, Write, AskUserQuestion, Bash]
---

# /analytics:roi-calculator

Calculate ROI for: **${ARGUMENTS:-automation}**

## Step 1: Gather Automation Data

Ask user:

```
Automation ROI Calculator

1. Manual Process Time (minutes per execution)
2. Automated Process Time (minutes per execution)
3. Frequency (times per day/week/month)
4. Implementation Cost (hours × hourly rate)
5. Operating Cost ($/month for APIs, hosting, etc.)
6. Hourly Rate (for time savings calculation)
```

## Step 2: Calculate Time Savings

```javascript
const timeSavingsPerExecution = manualTime - automatedTime;
const executionsPerMonth = frequency * 30; // normalize to monthly
const monthlyTimeSavings = timeSavingsPerExecution * executionsPerMonth;
const yearlyTimeSavings = monthlyTimeSavings * 12;
```

## Step 3: Calculate Cost Savings

```javascript
const monthlyLaborSavings = (monthlyTimeSavings / 60) * hourlyRate;
const monthlyNetSavings = monthlyLaborSavings - operatingCost;
const yearlyNetSavings = monthlyNetSavings * 12;
```

## Step 4: Calculate ROI Metrics

```javascript
const paybackPeriod = implementationCost / monthlyNetSavings;
const roi = ((yearlyNetSavings - implementationCost) / implementationCost) * 100;
const breakEvenDate = new Date();
breakEvenDate.setMonth(breakEvenDate.getMonth() + paybackPeriod);
```

## Step 5: Generate Report

```markdown
# 💰 ROI Analysis: ${automationName}

## Summary
- **ROI**: ${roi}% annually
- **Payback Period**: ${paybackPeriod.toFixed(1)} months
- **Break-Even Date**: ${breakEvenDate.toLocaleDateString()}

## Time Savings
- Per execution: ${timeSavingsPerExecution} minutes
- Per month: ${monthlyTimeSavings} minutes (${monthlyTimeSavings/60} hours)
- Per year: ${yearlyTimeSavings/60} hours

## Cost Analysis

### One-Time Costs
- Implementation: $${implementationCost}

### Monthly Costs
- Operating: $${operatingCost}
- Labor savings: $${monthlyLaborSavings}
- **Net savings**: $${monthlyNetSavings}

### Annual Value
- Year 1: $${year1Value}
- Year 2: $${year2Value}
- Year 3: $${year3Value}
- **3-Year Value**: $${threeYearValue}

## Comparison with Other Automations
${comparisons}

## Recommendation
${recommendation}
```

**Command Complete** 💰
