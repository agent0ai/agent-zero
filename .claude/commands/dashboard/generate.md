---
description: Generate custom analytics dashboard from data sources
argument-hint: <dashboard-name> [--sources <list>] [--format html|react|markdown] [--deploy local|vercel|github-pages]
model: claude-sonnet-4-5-20250929
allowed-tools: [Task, Read, Write, Bash, WebFetch]
---

# /dashboard:generate

Generate dashboard: **$ARGUMENTS**

## Step 1: Define Dashboard

Ask user:

```
Dashboard Configuration

1. Purpose (dev metrics, business KPIs, project health)
2. Data Sources (GitHub, Stripe, Database, APIs, logs)
3. Metrics to Track (commits, revenue, users, errors, etc.)
4. Refresh Frequency (real-time, hourly, daily)
5. Output Format (HTML, React component, Markdown)
```

## Step 2: Fetch Data from Sources

```javascript
const dataSources = {
  github: async () => {
    const issues = await gh('issue list --json number,title,state');
    const prs = await gh('pr list --json number,title,state');
    return { issues, prs };
  },
  stripe: async () => {
    const revenue = await stripe.charges.list({ limit: 100 });
    return { revenue };
  },
  database: async () => {
    const users = await db.query('SELECT COUNT(*) FROM users');
    return { users };
  }
};
```

## Step 3: Transform Data

```javascript
const metrics = {
  openIssues: data.github.issues.filter(i => i.state === 'open').length,
  mergedPRs: data.github.prs.filter(p => p.state === 'merged').length,
  revenue: data.stripe.revenue.reduce((sum, c) => sum + c.amount, 0) / 100,
  activeUsers: data.database.users[0].count
};
```

## Step 4: Generate Dashboard Code

**HTML Version**:

```html
<!DOCTYPE html>
<html>
<head>
  <title>${dashboardName}</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    .metric { padding: 20px; border: 1px solid #ddd; }
    .value { font-size: 2em; font-weight: bold; }
  </style>
</head>
<body>
  <h1>${dashboardName}</h1>
  <div class="metrics">
    ${metrics.map(m => `
      <div class="metric">
        <div class="label">${m.label}</div>
        <div class="value">${m.value}</div>
      </div>
    `).join('\n')}
  </div>

  <canvas id="chart"></canvas>

  <script>
    fetch('data.json')
      .then(r => r.json())
      .then(data => renderCharts(data));
  </script>
</body>
</html>
```

**React Version**:

```typescript
import React, { useEffect, useState } from 'react';

export function ${DashboardName}Dashboard() {
  const [metrics, setMetrics] = useState(null);

  useEffect(() => {
    fetch('/api/dashboard-data')
      .then(r => r.json())
      .then(setMetrics);
  }, []);

  return (
    <div className="dashboard">
      <h1>${dashboardName}</h1>
      ${widgets.map(w => `<${w.component} data={metrics.${w.data}} />`).join('\n')}
    </div>
  );
}
```

## Step 5: Create Data Fetching Script

```javascript
// fetch-dashboard-data.js
async function fetchAllData() {
  const data = await Promise.all([
    fetchGitHubData(),
    fetchStripeData(),
    fetchDatabaseData()
  ]);

  await fs.writeFile('public/data.json', JSON.stringify(data));
}

// Schedule refresh
if (refreshFrequency === 'hourly') {
  setInterval(fetchAllData, 60 * 60 * 1000);
}
```

## Step 6: Deploy Dashboard

**Local**:

```bash
open dashboard.html
```

**Vercel**:

```bash
vercel deploy --prod
```

**GitHub Pages**:

```bash
git checkout -b gh-pages
git add dashboard/
git commit -m "Add dashboard"
git push origin gh-pages
```

## Step 7: Summary

```markdown
# ✅ Dashboard Generated

## Files Created
- dashboard/${dashboardName}.html
- dashboard/data.json
- scripts/fetch-dashboard-data.js

## Deployment
${deploymentUrl ? `🌐 Live at: ${deploymentUrl}` : '📁 Local: dashboard/${dashboardName}.html'}

## Metrics Tracked
${metrics.map(m => `- ${m.label}`).join('\n')}

## Auto-Refresh
${refreshFrequency !== 'manual' ? `✅ Enabled (${refreshFrequency})` : '❌ Manual refresh only'}

## Next Steps
1. Customize styling in dashboard.css
2. Add more metrics
3. Configure alerts/notifications
```

**Command Complete** 📊
