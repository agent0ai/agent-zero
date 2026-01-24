---
description: Automated accessibility testing with axe-core, Lighthouse, and CI/CD integration
argument-hint: [--tool <axe|lighthouse|pa11y|all>] [--url <url>] [--ci] [--fail-on <critical|high|medium>]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Bash, Read, Write, Glob
---

Accessibility Testing: **${ARGUMENTS}**

## Automated Accessibility Testing

**Comprehensive accessibility testing** using industry-standard tools and best practices.

**Testing Tools**:

- **axe-core**: Deque Systems' accessibility engine (57% coverage)
- **Lighthouse**: Google's accessibility audit (40% coverage)
- **Pa11y**: HTML_CodeSniffer-based testing
- **Manual Testing Guide**: Keyboard, screen reader, zoom testing

**Capabilities**:

- Run automated accessibility tests
- Integrate with CI/CD pipelines
- Block builds on accessibility violations
- Generate test reports
- Track accessibility over time

Routes to **accessibility-auditor** agent:

```javascript
await Task({
  subagent_type: 'accessibility-auditor',
  description: 'Run accessibility tests',
  prompt: `Run comprehensive accessibility testing

Tool: ${TOOL || 'all'}
URL: ${URL || 'local development server'}
CI Mode: ${CI ? 'Yes - fail on violations' : 'No - report only'}
Fail Threshold: ${FAIL_ON || 'critical'}

Execute accessibility testing workflow:

## 1. Setup Testing Environment

### Install Testing Dependencies

\`\`\`bash
# axe-core (Deque Systems)
npm install --save-dev axe-core @axe-core/cli

# Lighthouse (Google)
npm install --save-dev lighthouse

# Pa11y (HTML_CodeSniffer)
npm install --save-dev pa11y

# Playwright (for automated browser testing)
npm install --save-dev @playwright/test
\`\`\`

### Create Test Configuration

\`\`\`javascript
// accessibility.config.js
module.exports = {
  tools: {
    axe: {
      enabled: true,
      rules: {
        // WCAG 2.1 Level AA rules
        'color-contrast': { enabled: true },
        'html-has-lang': { enabled: true },
        'image-alt': { enabled: true },
        'label': { enabled: true },
        'link-name': { enabled: true },
        'button-name': { enabled: true },
        'aria-required-children': { enabled: true },
        'aria-required-parent': { enabled: true },
        'aria-valid-attr': { enabled: true }
      },
      failThreshold: '${FAIL_ON || 'critical'}'
    },
    lighthouse: {
      enabled: true,
      categories: ['accessibility'],
      minScore: 90, // Target score for passing
      budgets: {
        accessibility: 90
      }
    },
    pa11y: {
      enabled: true,
      standard: 'WCAG2AA',
      threshold: {
        errors: 0,
        warnings: 10
      }
    }
  },
  ci: ${CI || false},
  reportPath: 'accessibility-tests/reports',
  failOn: '${FAIL_ON || 'critical'}' // critical, high, medium, low
};
\`\`\`

## 2. ${TOOL === 'axe' || TOOL === 'all' || !TOOL ? 'Run axe-core Tests' : ''}

${TOOL === 'axe' || TOOL === 'all' || !TOOL ? \`
### axe-core Testing (Deque Systems)

**Coverage**: 57% of WCAG issues detectable automatically

\`\`\`javascript
// tests/accessibility/axe.test.js
import { test, expect } from '@playwright/test';
import { injectAxe, checkA11y, getViolations } from 'axe-playwright';

test.describe('Accessibility Tests - axe-core', () => {

  test.beforeEach(async ({ page }) => {
    // Navigate to page
    await page.goto('${URL || 'http://localhost:3000'}');

    // Inject axe-core
    await injectAxe(page);
  });

  test('Home page has no accessibility violations', async ({ page }) => {
    await checkA11y(page, null, {
      detailedReport: true,
      detailedReportOptions: {
        html: true
      }
    });
  });

  test('Critical violations block build', async ({ page }) => {
    const violations = await getViolations(page);

    const criticalViolations = violations.filter(v =>
      v.impact === 'critical' || v.impact === 'serious'
    );

    ${CI ? \`
    // In CI mode, fail if critical violations found
    expect(criticalViolations).toHaveLength(0);
    \` : \`
    // In dev mode, just log violations
    if (criticalViolations.length > 0) {
      console.warn(\\\`Found \\\${criticalViolations.length} critical violations\\\`);
      criticalViolations.forEach(v => {
        console.warn(\\\`- \\\${v.help} (\\\${v.id})\\\`);
      });
    }
    \`}
  });

  test('Form elements are accessible', async ({ page }) => {
    await page.goto('${URL || 'http://localhost:3000'}/forms');

    await checkA11y(page, 'form', {
      rules: {
        'label': { enabled: true },
        'aria-required-children': { enabled: true },
        'autocomplete-valid': { enabled: true }
      }
    });
  });

  test('Navigation is keyboard accessible', async ({ page }) => {
    await page.goto('${URL || 'http://localhost:3000'}');

    // Tab through navigation
    await page.keyboard.press('Tab');
    const firstFocusedElement = await page.evaluate(() =>
      document.activeElement?.tagName
    );

    expect(firstFocusedElement).toBeTruthy();

    await checkA11y(page, 'nav');
  });

  test('Images have alt text', async ({ page }) => {
    await checkA11y(page, 'img', {
      rules: {
        'image-alt': { enabled: true }
      }
    });
  });

  test('Interactive elements are keyboard accessible', async ({ page }) => {
    await checkA11y(page, '[role="button"], [onClick]', {
      rules: {
        'button-name': { enabled: true },
        'tabindex': { enabled: true }
      }
    });
  });
});
\`\`\`

### Run axe-core CLI

\`\`\`bash
# Test single URL
npx axe ${URL || 'http://localhost:3000'} --reporter html --save accessibility-tests/reports/axe-report.html

# Test multiple pages
npx axe ${URL || 'http://localhost:3000'} \\
  ${URL || 'http://localhost:3000'}/about \\
  ${URL || 'http://localhost:3000'}/contact \\
  --reporter json --save accessibility-tests/reports/axe-results.json

${CI ? \`
# CI mode - fail on violations
npx axe ${URL || 'http://localhost:3000'} --exit
\` : ''}
\`\`\`
\` : ''}

## 3. ${TOOL === 'lighthouse' || TOOL === 'all' || !TOOL ? 'Run Lighthouse Tests' : ''}

${TOOL === 'lighthouse' || TOOL === 'all' || !TOOL ? \`
### Lighthouse Accessibility Audit (Google)

**Coverage**: 40% of WCAG issues detectable automatically

\`\`\`bash
# Run Lighthouse accessibility audit
lighthouse ${URL || 'http://localhost:3000'} \\
  --only-categories=accessibility \\
  --output html \\
  --output json \\
  --output-path accessibility-tests/reports/lighthouse-report

# View report
open accessibility-tests/reports/lighthouse-report.html
\`\`\`

\`\`\`javascript
// tests/accessibility/lighthouse.test.js
import lighthouse from 'lighthouse';
import * as chromeLauncher from 'chrome-launcher';

async function runLighthouseTest(url) {
  const chrome = await chromeLauncher.launch({ chromeFlags: ['--headless'] });
  const options = {
    logLevel: 'info',
    output: 'html',
    onlyCategories: ['accessibility'],
    port: chrome.port
  };

  const runnerResult = await lighthouse(url, options);

  await chrome.kill();

  return runnerResult;
}

test('Lighthouse accessibility score >= 90', async () => {
  const result = await runLighthouseTest('${URL || 'http://localhost:3000'}');

  const accessibilityScore = result.lhr.categories.accessibility.score * 100;

  console.log(\\\`Lighthouse Accessibility Score: \\\${accessibilityScore}/100\\\`);

  ${CI ? \`
  expect(accessibilityScore).toBeGreaterThanOrEqual(90);
  \` : \`
  if (accessibilityScore < 90) {
    console.warn('Accessibility score below target of 90');
  }
  \`}

  // Log failing audits
  const failedAudits = Object.values(result.lhr.audits)
    .filter(audit => audit.score !== null && audit.score < 1);

  failedAudits.forEach(audit => {
    console.log(\\\`❌ \\\${audit.title}: \\\${audit.description}\\\`);
  });
});
\`\`\`
\` : ''}

## 4. ${TOOL === 'pa11y' || TOOL === 'all' || !TOOL ? 'Run Pa11y Tests' : ''}

${TOOL === 'pa11y' || TOOL === 'all' || !TOOL ? \`
### Pa11y Testing (HTML_CodeSniffer)

\`\`\`bash
# Run Pa11y test
npx pa11y ${URL || 'http://localhost:3000'} \\
  --standard WCAG2AA \\
  --reporter json > accessibility-tests/reports/pa11y-results.json

${CI ? \`
# CI mode - fail on errors
npx pa11y ${URL || 'http://localhost:3000'} --standard WCAG2AA --threshold 0
\` : ''}
\`\`\`

\`\`\`javascript
// tests/accessibility/pa11y.test.js
import pa11y from 'pa11y';

test('Pa11y WCAG2AA compliance', async () => {
  const results = await pa11y('${URL || 'http://localhost:3000'}', {
    standard: 'WCAG2AA',
    includeNotices: true,
    includeWarnings: true
  });

  console.log(\\\`Pa11y Results: \\\${results.issues.length} issues found\\\`);

  const errors = results.issues.filter(i => i.type === 'error');
  const warnings = results.issues.filter(i => i.type === 'warning');

  console.log(\\\`Errors: \\\${errors.length}, Warnings: \\\${warnings.length}\\\`);

  ${CI ? \`
  expect(errors).toHaveLength(0);
  \` : \`
  if (errors.length > 0) {
    console.warn('Found accessibility errors');
    errors.forEach(err => {
      console.warn(\\\`- \\\${err.message} (Code: \\\${err.code})\\\`);
    });
  }
  \`}
});
\`\`\`
\` : ''}

## 5. Manual Testing Guide

\`\`\`markdown
# Manual Accessibility Testing Checklist

## Keyboard Navigation Testing

### ✅ Test All Interactive Elements
- [ ] Tab through entire page - all interactive elements receive focus
- [ ] Focus order matches visual order
- [ ] Focus indicators are visible (not outline: none)
- [ ] No keyboard traps (can exit all modals/dialogs with ESC)
- [ ] All functionality available via keyboard (no mouse-only interactions)
- [ ] Tab, Shift+Tab, Arrow keys, Enter, Space all work as expected

### ✅ Test Common Interactions
- [ ] Forms can be filled and submitted with keyboard only
- [ ] Dropdowns/select menus work with Arrow keys
- [ ] Modal dialogs trap focus and restore on close
- [ ] Accordions expand/collapse with Enter/Space
- [ ] Tabs switch with Arrow keys
- [ ] Custom controls (sliders, date pickers) are keyboard accessible

---

## Screen Reader Testing

Test with at least one screen reader:
- **Windows**: NVDA (free) or JAWS (commercial)
- **macOS**: VoiceOver (built-in)
- **Linux**: Orca (free)
- **Mobile**: TalkBack (Android), VoiceOver (iOS)

### ✅ Test Content Structure
- [ ] Page title is announced
- [ ] Headings hierarchy is logical and announced
- [ ] Landmarks (header, nav, main, footer) are announced
- [ ] Lists are announced correctly
- [ ] Tables have proper headers

### ✅ Test Interactive Elements
- [ ] Links announce link purpose clearly
- [ ] Buttons announce button label and role
- [ ] Form labels are associated and announced
- [ ] Error messages are announced
- [ ] Required fields are announced
- [ ] Image alt text is descriptive

### ✅ Test Dynamic Content
- [ ] Loading states are announced (aria-live)
- [ ] Error messages are announced
- [ ] Success messages are announced
- [ ] Content updates are announced (aria-live regions)

---

## Visual/Display Testing

### ✅ Zoom and Text Scaling
- [ ] Page readable at 200% zoom (no horizontal scroll)
- [ ] Page readable at 400% zoom (reflow acceptable)
- [ ] Text spacing can be increased without breaking layout
- [ ] No content is cut off when text is enlarged

### ✅ Color Contrast
- [ ] Text meets 4.5:1 contrast (normal text)
- [ ] Text meets 3:1 contrast (large text 18pt+)
- [ ] UI components meet 3:1 contrast
- [ ] Focus indicators meet 3:1 contrast
- [ ] Color is not the only visual means of conveying information

### ✅ Color Blindness
Test with color blindness simulators:
- [ ] Protanopia (red-blind)
- [ ] Deuteranopia (green-blind)
- [ ] Tritanopia (blue-blind)
- [ ] All information still understandable

---

## Mobile/Touch Testing

### ✅ Touch Targets
- [ ] All touch targets are at least 44x44 CSS pixels
- [ ] Touch targets have adequate spacing (not overlapping)
- [ ] Links and buttons are easy to tap

### ✅ Gestures
- [ ] Multi-touch gestures have single-touch alternatives
- [ ] Swipe gestures have button alternatives
- [ ] Pinch-to-zoom is not disabled (unless required for functionality)

---

## Form Testing

### ✅ Form Accessibility
- [ ] All inputs have associated labels
- [ ] Required fields marked with required or aria-required
- [ ] Error messages clearly identify the problem
- [ ] Error messages suggest how to fix
- [ ] Errors linked to fields with aria-describedby
- [ ] Success messages announced to screen readers
- [ ] Autocomplete attributes present for personal info

---

## Motion and Animation

### ✅ Respect User Preferences
- [ ] Respect prefers-reduced-motion setting
- [ ] No content flashes more than 3 times per second
- [ ] Auto-playing content can be paused
- [ ] Carousels have pause button

---

## Test Results Documentation

Document all findings in:
\`accessibility-tests/manual-test-results-\${DATE}.md\`
\`\`\`

## 6. Generate Test Report

\`\`\`markdown
# Accessibility Test Report

**Date**: \${new Date().toISOString().split('T')[0]}
**URL**: ${URL || 'Local Development'}
**CI Mode**: ${CI ? 'Yes' : 'No'}
**Fail Threshold**: ${FAIL_ON || 'critical'}

---

## 📊 Test Results Summary

| Tool | Score | Violations | Warnings | Status |
|------|-------|------------|----------|--------|
| **axe-core** | \${AXE_SCORE}/100 | \${AXE_VIOLATIONS} | \${AXE_WARNINGS} | ${CI ? '\${AXE_STATUS}' : 'Report'} |
| **Lighthouse** | \${LIGHTHOUSE_SCORE}/100 | \${LIGHTHOUSE_FAILURES} | - | ${CI ? '\${LIGHTHOUSE_STATUS}' : 'Report'} |
| **Pa11y** | - | \${PA11Y_ERRORS} | \${PA11Y_WARNINGS} | ${CI ? '\${PA11Y_STATUS}' : 'Report'} |

**Overall Status**: ${CI ? '\${OVERALL_STATUS}' : '📝 Report Generated'}

---

## 🔍 axe-core Results

**Violations**: \${AXE_VIOLATIONS}

### Critical Issues (\${AXE_CRITICAL})
\${axeCritical.map(v => \`
- **\${v.help}** (\\\`\${v.id}\\\`)
  - Impact: \${v.impact}
  - WCAG: \${v.tags.filter(t => t.startsWith('wcag')).join(', ')}
  - Affected Elements: \${v.nodes.length}
  - Fix: \${v.description}
\`).join('\\n')}

### High Priority Issues (\${AXE_HIGH})
\${axeHigh.map(v => \`
- **\${v.help}** (\\\`\${v.id}\\\`)
  - Affected Elements: \${v.nodes.length}
  - Fix: \${v.description}
\`).join('\\n')}

---

## 💡 Lighthouse Results

**Accessibility Score**: \${LIGHTHOUSE_SCORE}/100

### Failed Audits
\${lighthouseFailed.map(audit => \`
- **\${audit.title}**
  - Score: \${audit.score * 100}/100
  - Description: \${audit.description}
  - Fix: \${audit.recommendations}
\`).join('\\n')}

---

## 📋 Pa11y Results

**Errors**: \${PA11Y_ERRORS}
**Warnings**: \${PA11Y_WARNINGS}

### Errors
\${pa11yErrors.map(err => \`
- **\${err.message}**
  - Code: \${err.code}
  - Context: \${err.context}
  - Selector: \${err.selector}
\`).join('\\n')}

---

${CI ? \`
## 🚨 CI/CD Status

**Build Status**: \${OVERALL_STATUS}

\${OVERALL_STATUS === 'FAILED' ? \`
### ❌ Build Failed

The accessibility tests failed with violations exceeding the \\"${FAIL_ON}\\" threshold.

**Action Required**:
1. Review violations above
2. Run \\\`/accessibility/fix --auto-apply\\\` to fix common issues
3. Manually address remaining violations
4. Re-run tests: \\\`/accessibility/test --ci\\\`

**Violations Blocking Build**:
- Critical: \${CRITICAL_BLOCKING}
- High: \${HIGH_BLOCKING}

\` : \`
### ✅ Build Passed

All accessibility tests passed the \\"${FAIL_ON}\\" threshold.

**Quality Metrics**:
- axe-core: \${AXE_VIOLATIONS} violations
- Lighthouse: \${LIGHTHOUSE_SCORE}/100
- Pa11y: \${PA11Y_ERRORS} errors

\`}
\` : \`
## 📈 Recommendations

1. **Quick Fixes** (Run immediately):
   \\\`\\\`\\\`bash
   /accessibility/fix --auto-apply --severity critical
   \\\`\\\`\\\`

2. **Prioritize**:
   - Fix \${CRITICAL_COUNT} critical issues (blocks accessibility)
   - Fix \${HIGH_COUNT} high-priority issues (significantly impairs UX)

3. **Test Again**:
   \\\`\\\`\\\`bash
   /accessibility/test
   \\\`\\\`\\\`

4. **Enable CI/CD Integration**:
   \\\`\\\`\\\`bash
   /accessibility/test --ci --fail-on critical
   \\\`\\\`\\\`
\`}

---

## 📚 Next Steps

1. **Fix Issues**:
   \\\`\\\`\\\`bash
   /accessibility/fix --auto-apply
   \\\`\\\`\\\`

2. **Re-test**:
   \\\`\\\`\\\`bash
   /accessibility/test
   \\\`\\\`\\\`

3. **Manual Testing**:
   - Follow manual testing checklist above
   - Test with screen reader
   - Test keyboard navigation

4. **Continuous Monitoring**:
   - Add tests to CI/CD pipeline
   - Run tests before each deployment
   - Track scores over time

---

**Generated**: \${new Date().toLocaleString()}
**Test Tool**: Claude Code - Accessibility Auditor
\`\`\`

Save report to: accessibility-tests/reports/test-\${new Date().toISOString().split('T')[0]}.md
  `
})
```

## Usage Examples

```bash
# Run all accessibility tests
/accessibility/test

# Run specific tool
/accessibility/test --tool axe
/accessibility/test --tool lighthouse
/accessibility/test --tool pa11y

# Test remote URL
/accessibility/test --url https://example.com

# CI/CD mode (fail on violations)
/accessibility/test --ci --fail-on critical

# CI mode with high threshold
/accessibility/test --ci --fail-on high

# Run all tests in CI
/accessibility/test --tool all --ci --fail-on critical
```

## Testing Tools Comparison

| Tool | Coverage | Speed | Best For |
|------|----------|-------|----------|
| **axe-core** | 57% | Fast | Comprehensive WCAG testing |
| **Lighthouse** | 40% | Medium | Overall score + performance |
| **Pa11y** | 45% | Medium | HTML_CodeSniffer rules |
| **Manual** | 100% | Slow | True user experience validation |

**Recommendation**: Use all three automated tools + manual testing

## CI/CD Integration

### GitHub Actions

```yaml
name: Accessibility Tests

on: [push, pull_request]

jobs:
  a11y-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: npm ci

      - name: Start dev server
        run: npm run dev &
        env:
          CI: true

      - name: Wait for server
        run: npx wait-on http://localhost:3000

      - name: Run accessibility tests
        run: /accessibility/test --ci --fail-on critical

      - name: Upload test reports
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: accessibility-reports
          path: accessibility-tests/reports/
```

## Success Criteria

- ✓ axe-core: 0 critical violations
- ✓ Lighthouse: Score >= 90/100
- ✓ Pa11y: 0 errors
- ✓ Manual testing: All checklists passed

## When to Use

- **Pre-Commit**: Before committing code changes
- **Pre-Deployment**: Before deploying to production
- **CI/CD**: Automated testing in pipeline
- **Regular Audits**: Weekly or monthly checks
- **After Fixes**: Validate fixes with /accessibility/fix

## Time Savings

**Manual Testing**: 2-4 hours per full audit
**Automated Testing**: 2-5 minutes

**ROI**: Save 2-4 hours per test cycle

---

**Next Commands**: `/accessibility/audit` (detailed analysis), `/accessibility/fix` (apply fixes)
**CI/CD**: Add `--ci --fail-on critical` to block builds on violations
