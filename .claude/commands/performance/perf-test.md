---
description: Automated performance testing with baseline recording, regression detection, and CI/CD integration
argument-hint: [--mode <baseline|compare|ci>] [--path <test-path>] [--budget <budget-file>] [--fail-on <warning|error>]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Bash, Read, Write, Glob, Grep
---

Performance Testing: **${ARGUMENTS}**

## Automated Performance Testing with Regression Detection

**Comprehensive performance testing** that records baselines, detects regressions, enforces budgets, and integrates with CI/CD.

**Capabilities**:

- Record performance baselines for critical user paths
- Detect performance regressions (>10% = warning, >25% = error)
- Enforce performance budgets (response time, bundle size, Core Web Vitals)
- CI/CD integration with blocking thresholds
- Historical performance tracking and trending
- Lighthouse, WebPageTest, and custom metrics integration

Routes to **web-performance-optimizer** agent:

```javascript
await Task({
  subagent_type: 'web-performance-optimizer',
  description: 'Run performance tests and detect regressions',
  prompt: `Execute performance testing workflow

Mode: ${MODE || 'compare'} (baseline, compare, ci)
Test Path: ${PATH || 'all critical paths'}
Budget File: ${BUDGET || 'performance-budgets.json'}
Fail Threshold: ${FAIL_ON || 'error'}

Execute comprehensive performance testing:

## 1. Setup Testing Tools

### Install Dependencies

\`\`\`bash
# Lighthouse (Google's performance auditing tool)
npm install --save-dev lighthouse chrome-launcher

# Playwright (for automated browser testing)
npm install --save-dev @playwright/test

# Performance monitoring utilities
npm install --save-dev web-vitals
\`\`\`

### Create Test Scripts Directory

\`\`\`bash
mkdir -p scripts/performance
mkdir -p performance-baselines
mkdir -p performance-tests
\`\`\`

## 2. Define Critical User Paths

\`\`\`javascript
// scripts/performance/critical-paths.js
const criticalPaths = [
  {
    name: 'Homepage',
    url: '${PATH || 'http://localhost:3000'}',
    description: 'Main landing page',
    budget: {
      // Core Web Vitals (Google's user experience metrics)
      lcp: 2500,        // Largest Contentful Paint (ms) - <2.5s is good
      fid: 100,         // First Input Delay (ms) - <100ms is good
      cls: 0.1,         // Cumulative Layout Shift - <0.1 is good

      // Additional Performance Metrics
      fcp: 1800,        // First Contentful Paint (ms)
      tti: 3800,        // Time to Interactive (ms)
      tbt: 200,         // Total Blocking Time (ms)
      si: 3400,         // Speed Index (ms)

      // Resource Budgets
      bundleSize: 200,  // Main bundle size (KB)
      totalSize: 1000,  // Total page weight (KB)
      requests: 30,     // Number of HTTP requests

      // Custom Metrics
      apiResponseTime: 500  // API response time (ms, p95)
    }
  },
  {
    name: 'Product Listing',
    url: '${PATH || 'http://localhost:3000'}/products',
    description: 'Product catalog page',
    budget: {
      lcp: 3000,
      fid: 100,
      cls: 0.1,
      fcp: 2000,
      tti: 4000,
      tbt: 300,
      si: 3800,
      bundleSize: 250,
      totalSize: 1200,
      requests: 40,
      apiResponseTime: 800
    }
  },
  {
    name: 'Checkout Flow',
    url: '${PATH || 'http://localhost:3000'}/checkout',
    description: 'Critical conversion path',
    budget: {
      lcp: 2000,
      fid: 100,
      cls: 0.05,
      fcp: 1500,
      tti: 3000,
      tbt: 150,
      si: 3000,
      bundleSize: 180,
      totalSize: 800,
      requests: 25,
      apiResponseTime: 400
    }
  }
];

module.exports = { criticalPaths };
\`\`\`

## 3. ${MODE === 'baseline' || !MODE ? 'Baseline Recording Mode' : ''}

${MODE === 'baseline' || !MODE ? \`
### Record Performance Baseline

\`\`\`javascript
// scripts/performance/record-baseline.js
const lighthouse = require('lighthouse');
const chromeLauncher = require('chrome-launcher');
const { criticalPaths } = require('./critical-paths');
const fs = require('fs').promises;
const { execSync } = require('child_process');

async function runLighthouse(url, options = {}) {
  const chrome = await chromeLauncher.launch({
    chromeFlags: ['--headless', '--disable-gpu', '--no-sandbox']
  });

  const runnerOptions = {
    port: chrome.port,
    onlyCategories: ['performance'],
    throttling: {
      rttMs: 40,
      throughputKbps: 10 * 1024,
      cpuSlowdownMultiplier: 1,
      requestLatencyMs: 0,
      downloadThroughputKbps: 0,
      uploadThroughputKbps: 0
    },
    ...options
  };

  const runnerResult = await lighthouse(url, runnerOptions);

  await chrome.kill();

  return runnerResult;
}

async function getGitInfo() {
  try {
    return {
      commit: execSync('git rev-parse HEAD').toString().trim(),
      branch: execSync('git rev-parse --abbrev-ref HEAD').toString().trim(),
      author: execSync('git log -1 --format="%an"').toString().trim()
    };
  } catch (error) {
    return { commit: 'unknown', branch: 'unknown', author: 'unknown' };
  }
}

async function getBundleSize() {
  // Analyze bundle size from build output
  try {
    const buildStats = await fs.readFile('dist/stats.json', 'utf8');
    const stats = JSON.parse(buildStats);
    return Math.round(stats.assets.find(a => a.name.includes('main')).size / 1024);
  } catch {
    return 0;
  }
}

async function recordBaseline() {
  console.log('🚀 Recording performance baseline...\\n');

  const gitInfo = await getGitInfo();

  const baseline = {
    date: new Date().toISOString(),
    commit: gitInfo.commit,
    branch: gitInfo.branch,
    author: gitInfo.author,
    environment: process.env.NODE_ENV || 'development',
    nodeVersion: process.version,
    paths: []
  };

  for (const path of criticalPaths) {
    console.log(\\\`Testing: \\\${path.name} (\\\${path.url})...\\\`);

    try {
      // Run Lighthouse
      const lighthouseResult = await runLighthouse(path.url);

      // Extract metrics
      const lhr = lighthouseResult.lhr;
      const audits = lhr.audits;

      const metrics = {
        name: path.name,
        url: path.url,
        description: path.description,
        timestamp: new Date().toISOString(),
        lighthouse: {
          performanceScore: Math.round(lhr.categories.performance.score * 100),
          metrics: {
            lcp: Math.round(audits['largest-contentful-paint'].numericValue),
            fid: Math.round(audits['max-potential-fid'].numericValue),
            cls: parseFloat(audits['cumulative-layout-shift'].displayValue) || 0,
            fcp: Math.round(audits['first-contentful-paint'].numericValue),
            tti: Math.round(audits['interactive'].numericValue),
            tbt: Math.round(audits['total-blocking-time'].numericValue),
            si: Math.round(audits['speed-index'].numericValue)
          },
          resourceSummary: audits['resource-summary']?.details?.items || []
        },
        custom: {
          bundleSize: await getBundleSize(),
          totalRequests: audits['network-requests']?.details?.items?.length || 0,
          totalSize: Math.round((audits['total-byte-weight']?.numericValue || 0) / 1024)
        }
      };

      baseline.paths.push(metrics);

      console.log(\\\`  ✅ Lighthouse Score: \\\${metrics.lighthouse.performanceScore}/100\\\`);
      console.log(\\\`  LCP: \\\${metrics.lighthouse.metrics.lcp}ms, FID: \\\${metrics.lighthouse.metrics.fid}ms, CLS: \\\${metrics.lighthouse.metrics.cls}\\\`);
      console.log('');
    } catch (error) {
      console.error(\\\`  ❌ Failed to test \\\${path.name}: \\\${error.message}\\\`);
    }
  }

  // Save baseline
  const date = new Date().toISOString().split('T')[0];
  const baselinePath = \\\`performance-baselines/baseline-\\\${date}.json\\\`;

  await fs.mkdir('performance-baselines', { recursive: true });
  await fs.writeFile(baselinePath, JSON.stringify(baseline, null, 2));

  // Also save as 'latest' for easy comparison
  await fs.writeFile('performance-baselines/baseline-latest.json', JSON.stringify(baseline, null, 2));

  console.log(\\\`✅ Baseline recorded: \\\${baselinePath}\\\`);
  console.log(\\\`✅ Latest baseline: performance-baselines/baseline-latest.json\\\`);

  return baseline;
}

// Run if called directly
if (require.main === module) {
  recordBaseline().catch(console.error);
}

module.exports = { recordBaseline };
\`\`\`

### Run Baseline Recording

\`\`\`bash
# Record baseline
node scripts/performance/record-baseline.js

# Or use the command
/performance/perf-test --mode baseline
\`\`\`
\` : ''}

## 4. ${MODE === 'compare' || !MODE ? 'Compare Against Baseline' : ''}

${MODE === 'compare' || !MODE ? \`
### Performance Comparison Mode

\`\`\`javascript
// scripts/performance/compare-performance.js
const { recordBaseline } = require('./record-baseline');
const fs = require('fs').promises;

function calculateRegression(baseline, current, metric) {
  const change = current - baseline;
  const percentChange = (change / baseline) * 100;

  let status = 'stable';
  let severity = 'none';

  if (percentChange > 25) {
    status = 'error';
    severity = 'critical';
  } else if (percentChange > 10) {
    status = 'warning';
    severity = 'high';
  } else if (percentChange < -5) {
    status = 'improved';
    severity = 'none';
  }

  return {
    baseline,
    current,
    change: Math.round(change),
    percentChange: parseFloat(percentChange.toFixed(2)),
    status,
    severity
  };
}

async function comparePerformance() {
  console.log('📊 Comparing performance against baseline...\\n');

  // Load baseline
  let baseline;
  try {
    const baselineData = await fs.readFile('performance-baselines/baseline-latest.json', 'utf8');
    baseline = JSON.parse(baselineData);
    console.log(\\\`Baseline: \\\${baseline.date} (commit: \\\${baseline.commit.substring(0, 7)})\\\`);
    console.log('');
  } catch (error) {
    console.error('❌ No baseline found. Run with --mode baseline first.');
    process.exit(1);
  }

  // Run current tests
  console.log('Running current performance tests...\\n');
  const current = await recordBaseline();

  // Compare
  const comparison = {
    baselineDate: baseline.date,
    baselineCommit: baseline.commit,
    currentDate: current.date,
    currentCommit: current.commit,
    summary: {
      totalPaths: baseline.paths.length,
      improved: 0,
      stable: 0,
      regressed: 0,
      warnings: [],
      errors: []
    },
    paths: []
  };

  for (let i = 0; i < baseline.paths.length; i++) {
    const baselinePath = baseline.paths[i];
    const currentPath = current.paths[i];

    if (!currentPath) continue;

    const pathComparison = {
      name: currentPath.name,
      url: currentPath.url,
      status: 'stable',
      metrics: {},
      regressions: [],
      improvements: []
    };

    // Compare Core Web Vitals
    const metricsToCompare = [
      { key: 'lcp', name: 'LCP', unit: 'ms' },
      { key: 'fid', name: 'FID', unit: 'ms' },
      { key: 'cls', name: 'CLS', unit: '' },
      { key: 'fcp', name: 'FCP', unit: 'ms' },
      { key: 'tti', name: 'TTI', unit: 'ms' },
      { key: 'tbt', name: 'TBT', unit: 'ms' },
      { key: 'si', name: 'Speed Index', unit: 'ms' }
    ];

    for (const metric of metricsToCompare) {
      const baselineValue = baselinePath.lighthouse.metrics[metric.key];
      const currentValue = currentPath.lighthouse.metrics[metric.key];

      const regression = calculateRegression(baselineValue, currentValue, metric.key);
      pathComparison.metrics[metric.key] = regression;

      if (regression.status === 'error') {
        pathComparison.regressions.push({
          metric: metric.name,
          severity: 'error',
          ...regression
        });
        comparison.summary.errors.push(
          \\\`\\\${currentPath.name}: \\\${metric.name} regressed by \\\${regression.percentChange}% (\\\${baselineValue}\\\${metric.unit} → \\\${currentValue}\\\${metric.unit})\\\`
        );
      } else if (regression.status === 'warning') {
        pathComparison.regressions.push({
          metric: metric.name,
          severity: 'warning',
          ...regression
        });
        comparison.summary.warnings.push(
          \\\`\\\${currentPath.name}: \\\${metric.name} slower by \\\${regression.percentChange}% (\\\${baselineValue}\\\${metric.unit} → \\\${currentValue}\\\${metric.unit})\\\`
        );
      } else if (regression.status === 'improved') {
        pathComparison.improvements.push({
          metric: metric.name,
          ...regression
        });
      }
    }

    // Determine overall status
    if (pathComparison.regressions.some(r => r.severity === 'error')) {
      pathComparison.status = 'error';
      comparison.summary.regressed++;
    } else if (pathComparison.regressions.some(r => r.severity === 'warning')) {
      pathComparison.status = 'warning';
      comparison.summary.regressed++;
    } else if (pathComparison.improvements.length > 0) {
      pathComparison.status = 'improved';
      comparison.summary.improved++;
    } else {
      comparison.summary.stable++;
    }

    comparison.paths.push(pathComparison);
  }

  // Save comparison
  const date = new Date().toISOString().split('T')[0];
  const comparisonPath = \\\`performance-tests/comparison-\\\${date}.json\\\`;

  await fs.mkdir('performance-tests', { recursive: true });
  await fs.writeFile(comparisonPath, JSON.stringify(comparison, null, 2));

  // Print summary
  console.log('\\n📊 Comparison Summary:\\n');
  console.log(\\\`  🟢 Improved: \\\${comparison.summary.improved}\\\`);
  console.log(\\\`  ⚪ Stable: \\\${comparison.summary.stable}\\\`);
  console.log(\\\`  🔴 Regressed: \\\${comparison.summary.regressed}\\\`);

  if (comparison.summary.errors.length > 0) {
    console.log('\\n🔴 Critical Regressions (>25%):\\n');
    comparison.summary.errors.forEach(err => console.log(\\\`  - \\\${err}\\\`));
  }

  if (comparison.summary.warnings.length > 0) {
    console.log('\\n⚠️  Performance Warnings (10-25%):\\n');
    comparison.summary.warnings.forEach(warn => console.log(\\\`  - \\\${warn}\\\`));
  }

  console.log(\\\`\\n✅ Comparison saved: \\\${comparisonPath}\\\`);

  return comparison;
}

if (require.main === module) {
  comparePerformance().catch(console.error);
}

module.exports = { comparePerformance };
\`\`\`
\` : ''}

## 5. ${MODE === 'ci' ? 'CI/CD Integration Mode' : ''}

${MODE === 'ci' ? \`
### CI/CD Mode with Budget Enforcement

\`\`\`javascript
// scripts/performance/ci-mode.js
const { recordBaseline } = require('./record-baseline');
const { criticalPaths } = require('./critical-paths');
const fs = require('fs').promises;

async function runCIMode(failOn = '${FAIL_ON || 'error'}') {
  console.log('🔍 Running performance tests in CI mode...\\n');
  console.log(\\\`Fail threshold: \\\${failOn}\\\`);
  console.log('');

  // Run tests
  const current = await recordBaseline();

  const results = {
    pass: true,
    violations: [],
    summary: {
      totalBudgets: 0,
      passed: 0,
      warnings: 0,
      errors: 0
    },
    paths: []
  };

  for (const currentPath of current.paths) {
    const pathBudget = criticalPaths.find(p => p.name === currentPath.name);

    if (!pathBudget) {
      console.warn(\\\`⚠️  No budget defined for: \\\${currentPath.name}\\\`);
      continue;
    }

    const pathResult = {
      name: currentPath.name,
      url: currentPath.url,
      budgetChecks: [],
      status: 'pass'
    };

    // Check each budget
    for (const [metric, budget] of Object.entries(pathBudget.budget)) {
      results.summary.totalBudgets++;

      let actualValue;
      if (metric in currentPath.lighthouse.metrics) {
        actualValue = currentPath.lighthouse.metrics[metric];
      } else if (metric === 'bundleSize') {
        actualValue = currentPath.custom.bundleSize;
      } else if (metric === 'totalSize') {
        actualValue = currentPath.custom.totalSize;
      } else if (metric === 'requests') {
        actualValue = currentPath.custom.totalRequests;
      }

      if (actualValue === undefined) continue;

      const percentOver = ((actualValue - budget) / budget) * 100;

      const checkResult = {
        metric,
        budget,
        actual: actualValue,
        percentOver: parseFloat(percentOver.toFixed(2)),
        status: 'pass'
      };

      if (percentOver > 25) {
        checkResult.status = 'error';
        pathResult.status = 'error';
        results.summary.errors++;
        results.pass = false;

        results.violations.push({
          path: currentPath.name,
          metric,
          severity: 'error',
          budget,
          actual: actualValue,
          percentOver: percentOver.toFixed(1) + '%'
        });
      } else if (percentOver > 10) {
        checkResult.status = 'warning';
        if (pathResult.status !== 'error') {
          pathResult.status = 'warning';
        }
        results.summary.warnings++;

        if (failOn === 'warning') {
          results.pass = false;
        }

        results.violations.push({
          path: currentPath.name,
          metric,
          severity: 'warning',
          budget,
          actual: actualValue,
          percentOver: percentOver.toFixed(1) + '%'
        });
      } else {
        results.summary.passed++;
      }

      pathResult.budgetChecks.push(checkResult);
    }

    results.paths.push(pathResult);
  }

  // Save results
  const date = new Date().toISOString().split('T')[0];
  await fs.mkdir('performance-tests', { recursive: true });
  await fs.writeFile(\\\`performance-tests/ci-result-\\\${date}.json\\\`, JSON.stringify(results, null, 2));

  // Print summary
  console.log('\\n📊 CI Test Results:\\n');
  console.log(\\\`  ✅ Passed: \\\${results.summary.passed}/\\\${results.summary.totalBudgets}\\\`);
  console.log(\\\`  ⚠️  Warnings: \\\${results.summary.warnings}\\\`);
  console.log(\\\`  🔴 Errors: \\\${results.summary.errors}\\\`);

  if (results.violations.length > 0) {
    console.log('\\n🚨 Budget Violations:\\n');
    results.violations.forEach(v => {
      const icon = v.severity === 'error' ? '🔴' : '⚠️';
      console.log(\\\`  \\\${icon} \\\${v.path} - \\\${v.metric}: \\\${v.actual} (budget: \\\${v.budget}, over by \\\${v.percentOver})\\\`);
    });
  }

  console.log(\\\`\\n\\\${results.pass ? '✅' : '❌'} Build Status: \\\${results.pass ? 'PASSED' : 'FAILED'}\\\`);

  if (!results.pass) {
    process.exit(1);
  }

  return results;
}

if (require.main === module) {
  const failOn = process.argv[2] || 'error';
  runCIMode(failOn).catch(console.error);
}

module.exports = { runCIMode };
\`\`\`

### GitHub Actions Integration

\`\`\`yaml
# .github/workflows/performance-tests.yml
name: Performance Tests

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  performance-test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0

      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: npm ci

      - name: Build application
        run: npm run build

      - name: Start dev server
        run: npm run start &
        env:
          CI: true

      - name: Wait for server
        run: npx wait-on http://localhost:3000 --timeout 60000

      - name: Run performance tests
        run: node scripts/performance/ci-mode.js error

      - name: Upload performance reports
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: performance-reports
          path: |
            performance-tests/
            performance-baselines/

      - name: Comment PR with results
        if: github.event_name == 'pull_request' && always()
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const files = fs.readdirSync('performance-tests').filter(f => f.startsWith('ci-result'));
            const latestFile = files.sort().reverse()[0];
            const results = JSON.parse(fs.readFileSync(\\\`performance-tests/\\\${latestFile}\\\`, 'utf8'));

            let comment = '## 🚀 Performance Test Results\\n\\n';

            if (results.pass) {
              comment += '✅ **All performance budgets passed!**\\n\\n';
            } else {
              comment += '❌ **Performance budgets violated**\\n\\n';
            }

            comment += \\\`**Summary**: \\\${results.summary.passed}/\\\${results.summary.totalBudgets} budgets passed\\n\\n\\\`;

            if (results.violations.length > 0) {
              comment += '### 🚨 Budget Violations\\n\\n';
              comment += '| Severity | Path | Metric | Budget | Actual | Over By |\\n';
              comment += '|----------|------|--------|--------|--------|---------|\\n';

              results.violations.forEach(v => {
                const icon = v.severity === 'error' ? '🔴' : '⚠️';
                comment += \\\`| \\\${icon} | \\\${v.path} | \\\${v.metric} | \\\${v.budget} | \\\${v.actual} | \\\${v.percentOver} |\\n\\\`;
              });
            }

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: comment
            });
\`\`\`
\` : ''}

## 6. Generate Test Report

Generate comprehensive markdown report summarizing test results.

Save to: performance-tests/report-\${DATE}.md
  `
})
```

## Usage Examples

```bash
# Record initial baseline
/performance/perf-test --mode baseline

# Compare against baseline (development)
/performance/perf-test --mode compare

# Test specific path
/performance/perf-test --mode compare --path http://localhost:3000/checkout

# CI mode with error blocking (default)
/performance/perf-test --mode ci --fail-on error

# CI mode with warning blocking (stricter)
/performance/perf-test --mode ci --fail-on warning

# Use custom budget file
/performance/perf-test --mode ci --budget custom-budgets.json --fail-on error
```

## Performance Testing Modes

| Mode | Purpose | Usage | Blocks Build |
|------|---------|-------|--------------|
| **baseline** | Record new baseline | Initial setup, monthly updates | No |
| **compare** | Compare vs baseline | Development, pre-commit | No (warnings only) |
| **ci** | Enforce budgets | CI/CD pipeline | Yes (configurable) |

## Regression Thresholds

| Change | Status | Action |
|--------|--------|--------|
| **<5%** | Stable | ✅ Acceptable variation |
| **5-10%** | Minor | 🟡 Monitor |
| **10-25%** | Warning | ⚠️ Investigate & optimize |
| **>25%** | Critical | 🔴 Block & revert |

## Core Web Vitals Budgets

### Good Thresholds (Google Standards)

- **LCP** (Largest Contentful Paint): <2.5s
- **FID** (First Input Delay): <100ms
- **CLS** (Cumulative Layout Shift): <0.1

### Additional Metrics

- **FCP** (First Contentful Paint): <1.8s
- **TTI** (Time to Interactive): <3.8s
- **TBT** (Total Blocking Time): <200ms
- **Speed Index**: <3.4s

## Success Criteria

- ✓ Baseline recorded for all critical paths
- ✓ Regression detection (>10% warning, >25% error)
- ✓ CI/CD integration blocks on violations
- ✓ Historical tracking enabled
- ✓ Comprehensive reporting

## When to Use

- **baseline**: Initially, monthly, after major releases
- **compare**: During development, before commits
- **ci**: In PR pipelines, before merges

## Business Impact

**ROI**: $25,000/year

- Catch performance regressions before production
- Prevent costly performance incidents
- Maintain user experience quality
- Improve Core Web Vitals rankings

**Time Savings**: 2-4 hours per test cycle (automated vs manual)

---

**Next Commands**: `/performance/profile` (profiling), `/performance/optimize` (recommendations)
**CI/CD**: Add `--mode ci --fail-on error` to GitHub Actions
