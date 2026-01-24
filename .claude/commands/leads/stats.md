---
description: View lead generation statistics and analytics for an organization
argument-hint: [organization-id] [--period 7d|30d|90d]
allowed-tools: [Bash, Read]
---

# Lead Generation Statistics

View comprehensive statistics about discovered leads, qualification rates, and outreach performance.

## Usage

```bash
/leads/stats [organization-id] [--period <time-period>]
```

## Arguments

- `organization-id`: The organization UUID (required)
- `--period`: Time period for statistics (optional, default: 30d)
  - `7d`: Last 7 days
  - `30d`: Last 30 days
  - `90d`: Last 90 days

## Example Output

```
📊 Lead Generation Statistics
Organization: Mahoosuc Solutions
Period: Last 30 days

🔎 Discovery Metrics:
   - Total Discovered: 342 leads
   - By Platform:
     • Reddit: 156 leads (45.6%)
     • Stack Overflow: 98 leads (28.7%)
     • HackerNews: 52 leads (15.2%)
     • Dev.to: 36 leads (10.5%)

🤖 Qualification Metrics:
   - Total Qualified: 187 leads (54.7%)
   - Average Score: 68.2/100
   - Grade Distribution:
     • A+ (95-100): 12 leads (6.4%)
     • A (85-94): 34 leads (18.2%)
     • B+ (75-84): 56 leads (29.9%)
     • B (65-74): 48 leads (25.7%)
     • C+ (55-64): 37 leads (19.8%)

📤 Outreach Metrics:
   - Messages Sent: 89 messages
   - Response Rate: 31.5%
   - Positive Responses: 18 (20.2%)
   - Opt-Outs: 2 (2.2%)

🎯 CRM Sync:
   - Leads Synced: 65 leads
   - Contacts Created: 12 contacts
   - Deals Created: 3 deals
   - Sync Success Rate: 98.5%

💰 Cost Analysis:
   - Claude AI Calls: 34
   - Total Cost: $0.11
   - Cost per Qualified Lead: $0.0006
```
