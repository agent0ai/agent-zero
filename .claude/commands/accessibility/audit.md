---
description: Comprehensive WCAG 2.1/2.2 accessibility compliance audit with scoring and auto-fix recommendations
argument-hint: [--url <url>] [--level <A|AA|AAA>] [--format <json|markdown|html>]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Read, Glob, Grep, WebFetch, Write
---

Accessibility Audit: **${ARGUMENTS}**

## WCAG 2.1/2.2 Compliance Audit

**Comprehensive accessibility audit** for web applications, following Web Content Accessibility Guidelines (WCAG) 2.1 and 2.2.

**Generates**:

- Overall accessibility score (0-100)
- Detailed findings by WCAG principle
- Severity categorization (Critical, High, Medium, Low)
- Auto-fix recommendations with code examples
- Compliance level assessment (A, AA, AAA)
- Actionable remediation roadmap

Routes to **accessibility-auditor** agent:

```javascript
await Task({
  subagent_type: 'accessibility-auditor',
  description: 'WCAG 2.1/2.2 compliance audit',
  prompt: `Perform comprehensive accessibility audit for: ${URL || 'current codebase'}

Compliance Level: ${LEVEL || 'AA'} (default: AA for production)
Output Format: ${FORMAT || 'markdown'}

Execute comprehensive WCAG 2.1/2.2 accessibility audit:

## 1. Identify Audit Scope

${URL ? \`
### Remote URL Audit
- Target URL: \${URL}
- Fetch page content using WebFetch
- Extract HTML, CSS, and accessible DOM
\` : \`
### Local Codebase Audit
- Scan for web-accessible files (HTML, JSX, TSX, Vue, Svelte)
- Identify component files and templates
- Extract rendered markup patterns
\`}

### File Discovery

Use Glob to find all web interface files:

\`\`\`javascript
const webFiles = [
  '**/*.html',
  '**/*.jsx',
  '**/*.tsx',
  '**/*.vue',
  '**/*.svelte',
  'src/components/**/*',
  'src/pages/**/*',
  'public/**/*.html'
];
\`\`\`

## 2. WCAG 2.1/2.2 Principles Analysis

Audit against all 4 WCAG principles:

### Principle 1: Perceivable
Information and UI components must be presentable to users in ways they can perceive.

#### 1.1 Text Alternatives (Level A)
**Guidelines**:
- 1.1.1: All non-text content has text alternative

**Check for**:
\`\`\`javascript
const textAlternativesChecks = {
  images: {
    check: 'All <img> tags have alt attribute',
    pattern: /<img(?![^>]*alt=)/gi,
    severity: 'Critical',
    wcagLevel: 'A',
    autoFix: 'Add alt="" for decorative images, descriptive alt text for meaningful images'
  },
  icons: {
    check: 'Icon fonts have aria-label or aria-hidden',
    pattern: /<i class=["'](?:fa|icon|material-icons)/gi,
    severity: 'High',
    wcagLevel: 'A',
    autoFix: 'Add aria-label for meaningful icons, aria-hidden="true" for decorative'
  },
  svgs: {
    check: 'SVGs have <title> or role="img" with aria-label',
    pattern: /<svg(?![^>]*(?:role=|aria-label=|<title>))/gi,
    severity: 'High',
    wcagLevel: 'A',
    autoFix: 'Add <title> element inside SVG or role="img" with aria-label'
  },
  buttons: {
    check: 'Icon-only buttons have accessible names',
    pattern: /<button[^>]*>\\s*<(?:i|svg|span class=["']icon)/gi,
    severity: 'Critical',
    wcagLevel: 'A',
    autoFix: 'Add aria-label or visually-hidden text inside button'
  }
};
\`\`\`

#### 1.2 Time-based Media (Level A, AA)
**Guidelines**:
- 1.2.1: Captions for prerecorded audio
- 1.2.2: Audio descriptions for prerecorded video
- 1.2.5: Audio descriptions for prerecorded video (AA)

**Check for**:
\`\`\`javascript
const mediaChecks = {
  video: {
    check: '<video> elements have captions track',
    pattern: /<video(?![^>]*<track[^>]*kind=["']captions)/gi,
    severity: 'High',
    wcagLevel: 'A',
    autoFix: 'Add <track kind="captions" src="captions.vtt" srclang="en">'
  },
  audio: {
    check: '<audio> elements have transcripts',
    severity: 'Medium',
    wcagLevel: 'A',
    autoFix: 'Provide transcript link near audio element'
  }
};
\`\`\`

#### 1.3 Adaptable (Level A, AA)
**Guidelines**:
- 1.3.1: Info and relationships programmatically determined
- 1.3.2: Meaningful sequence preserved
- 1.3.4: Orientation not restricted (AA)
- 1.3.5: Identify input purpose (AA)

**Check for**:
\`\`\`javascript
const adaptableChecks = {
  semanticHTML: {
    check: 'Use semantic HTML elements instead of divs',
    issues: [
      { pattern: /<div[^>]*role=["']button["']/gi, fix: 'Use <button> instead of <div role="button">' },
      { pattern: /<div[^>]*role=["']link["']/gi, fix: 'Use <a> instead of <div role="link">' },
      { pattern: /<div[^>]*role=["']heading["']/gi, fix: 'Use <h1-h6> instead of <div role="heading">' }
    ],
    severity: 'Medium',
    wcagLevel: 'A'
  },
  headingHierarchy: {
    check: 'Heading levels follow logical hierarchy',
    autoFix: 'Ensure h1 → h2 → h3 (no skipping levels)',
    severity: 'Medium',
    wcagLevel: 'A'
  },
  formLabels: {
    check: 'All form inputs have associated labels',
    pattern: /<input(?![^>]*(?:aria-label=|aria-labelledby=|id=["'][^"']*["'][^>]*>\\s*<label[^>]*for=))/gi,
    severity: 'Critical',
    wcagLevel: 'A',
    autoFix: 'Add <label for="input-id"> or aria-label attribute'
  },
  landmarks: {
    check: 'Page uses ARIA landmarks or HTML5 sectioning',
    required: ['<main>', '<nav>', '<header>', '<footer>'],
    severity: 'Medium',
    wcagLevel: 'A',
    autoFix: 'Add semantic HTML5 elements: <header>, <nav>, <main>, <aside>, <footer>'
  },
  autocomplete: {
    check: 'Form inputs have autocomplete attribute for personal info',
    fields: ['name', 'email', 'tel', 'street-address', 'postal-code', 'cc-number'],
    severity: 'Medium',
    wcagLevel: 'AA',
    autoFix: 'Add autocomplete="email" to email inputs, autocomplete="name" to name inputs'
  }
};
\`\`\`

#### 1.4 Distinguishable (Level A, AA, AAA)
**Guidelines**:
- 1.4.1: Use of color is not the only visual means
- 1.4.3: Color contrast ratio at least 4.5:1 (AA)
- 1.4.6: Color contrast ratio at least 7:1 (AAA)
- 1.4.10: Reflow without horizontal scrolling at 320px (AA)
- 1.4.11: Non-text contrast at least 3:1 (AA)
- 1.4.12: Text spacing adjustable (AA)
- 1.4.13: Hover/focus content (AA)

**Check for**:
\`\`\`javascript
const distinguishableChecks = {
  colorContrast: {
    check: 'Text color contrast meets WCAG ${LEVEL === 'AAA' ? '7:1' : '4.5:1'}',
    severity: 'Critical',
    wcagLevel: '${LEVEL === 'AAA' ? 'AAA' : 'AA'}',
    autoFix: \`
      // Use color contrast checker
      function checkContrast(foreground, background) {
        const ratio = calculateContrastRatio(foreground, background);
        const target = ${LEVEL === 'AAA' ? '7.0' : '4.5'};
        return {
          passes: ratio >= target,
          ratio: ratio.toFixed(2),
          recommendation: ratio < target ? suggestBetterColor(foreground, background, target) : null
        };
      }
    \`
  },
  focusVisible: {
    check: 'Focus indicators visible and meet 3:1 contrast',
    pattern: /(:focus\\s*{[^}]*outline:\\s*none)/gi,
    severity: 'Critical',
    wcagLevel: 'AA',
    autoFix: 'Remove outline: none or add custom focus style with 3:1 contrast'
  },
  nonTextContrast: {
    check: 'UI components and graphics have 3:1 contrast',
    components: ['buttons', 'form borders', 'icons', 'charts'],
    severity: 'High',
    wcagLevel: 'AA',
    autoFix: 'Ensure borders, icons, and interactive elements have 3:1 contrast'
  },
  textSpacing: {
    check: 'Text remains readable when spacing is increased',
    requirements: {
      lineHeight: '1.5x font size',
      paragraphSpacing: '2x font size',
      letterSpacing: '0.12x font size',
      wordSpacing: '0.16x font size'
    },
    severity: 'Medium',
    wcagLevel: 'AA',
    autoFix: 'Avoid fixed heights on text containers, use min-height instead'
  },
  reflow: {
    check: 'Content reflows at 320px width without horizontal scroll',
    severity: 'High',
    wcagLevel: 'AA',
    autoFix: 'Use responsive design, avoid fixed widths, test at 320px viewport'
  }
};
\`\`\`

---

### Principle 2: Operable
User interface components and navigation must be operable.

#### 2.1 Keyboard Accessible (Level A)
**Guidelines**:
- 2.1.1: All functionality available via keyboard
- 2.1.2: No keyboard trap
- 2.1.4: Character key shortcuts (A)

**Check for**:
\`\`\`javascript
const keyboardChecks = {
  clickHandlers: {
    check: 'Elements with onClick have keyboard handlers',
    pattern: /<(?:div|span)[^>]*onClick=/gi,
    severity: 'Critical',
    wcagLevel: 'A',
    autoFix: 'Add onKeyDown handler or use <button> instead of <div onClick>'
  },
  tabIndex: {
    check: 'Custom interactive elements have tabindex',
    pattern: /<div[^>]*role=["'](?:button|link|tab)["'](?![^>]*tabindex=)/gi,
    severity: 'Critical',
    wcagLevel: 'A',
    autoFix: 'Add tabindex="0" to make element keyboard focusable'
  },
  keyboardTrap: {
    check: 'Modal dialogs allow keyboard exit',
    severity: 'Critical',
    wcagLevel: 'A',
    autoFix: 'Add ESC key handler to close modals, ensure focus returns to trigger'
  },
  skipLinks: {
    check: 'Page has "Skip to main content" link',
    severity: 'Medium',
    wcagLevel: 'A',
    autoFix: 'Add <a href="#main" class="skip-link">Skip to main content</a> as first element'
  }
};
\`\`\`

#### 2.2 Enough Time (Level A, AA)
**Guidelines**:
- 2.2.1: Timing adjustable
- 2.2.2: Pause, stop, hide for auto-updating content

**Check for**:
\`\`\`javascript
const timingChecks = {
  autoplay: {
    check: 'Auto-playing content can be paused',
    pattern: /<(?:video|audio)[^>]*autoplay/gi,
    severity: 'High',
    wcagLevel: 'A',
    autoFix: 'Add controls, or pause/play button for auto-playing media'
  },
  carousels: {
    check: 'Auto-advancing carousels have pause button',
    severity: 'High',
    wcagLevel: 'A',
    autoFix: 'Add pause/play button, pause on hover/focus'
  },
  sessionTimeout: {
    check: 'Session timeouts warn users and allow extension',
    severity: 'Medium',
    wcagLevel: 'A',
    autoFix: 'Show warning 2 minutes before timeout, allow extension'
  }
};
\`\`\`

#### 2.3 Seizures (Level A, AA)
**Guidelines**:
- 2.3.1: No content flashes more than 3 times per second

**Check for**:
\`\`\`javascript
const seizureChecks = {
  animations: {
    check: 'Animations do not flash more than 3 times/second',
    pattern: /animation.*blink|animation.*flash/gi,
    severity: 'Critical',
    wcagLevel: 'A',
    autoFix: 'Reduce animation frequency to <3 flashes/second'
  }
};
\`\`\`

#### 2.4 Navigable (Level A, AA)
**Guidelines**:
- 2.4.1: Bypass blocks of repeated content
- 2.4.2: Pages have titles
- 2.4.3: Focus order is logical
- 2.4.4: Link purpose clear from text
- 2.4.6: Headings and labels are descriptive (AA)
- 2.4.7: Focus visible (AA)

**Check for**:
\`\`\`javascript
const navigableChecks = {
  pageTitle: {
    check: 'Page has unique, descriptive <title>',
    pattern: /<title>(?:Untitled|Document|Page)?<\\/title>/gi,
    severity: 'High',
    wcagLevel: 'A',
    autoFix: 'Add descriptive title: <title>Page Name - Site Name</title>'
  },
  linkText: {
    check: 'Links have descriptive text (not "click here")',
    pattern: />\\s*(?:click here|read more|here|more)\\s*</gi,
    severity: 'Medium',
    wcagLevel: 'A',
    autoFix: 'Use descriptive link text: "Read our accessibility policy" instead of "click here"'
  },
  headings: {
    check: 'Headings are descriptive and informative',
    severity: 'Medium',
    wcagLevel: 'AA',
    autoFix: 'Use clear headings: "Contact Information" instead of "Info"'
  },
  focusOrder: {
    check: 'Focus order matches visual order',
    severity: 'High',
    wcagLevel: 'A',
    autoFix: 'Avoid positive tabindex values, use CSS for visual reordering instead of DOM manipulation'
  }
};
\`\`\`

#### 2.5 Input Modalities (Level A, AA)
**Guidelines**:
- 2.5.1: Pointer gestures have single-pointer alternative
- 2.5.2: Pointer cancellation (A)
- 2.5.3: Label in name (A)
- 2.5.4: Motion actuation (A)

**Check for**:
\`\`\`javascript
const inputModalitiesChecks = {
  touchTargets: {
    check: 'Touch targets are at least 44x44 CSS pixels',
    severity: 'High',
    wcagLevel: 'AA (WCAG 2.2)',
    autoFix: 'Increase button/link size or padding to meet 44x44px minimum'
  },
  gestureAlternatives: {
    check: 'Multi-point gestures have single-pointer alternatives',
    severity: 'Medium',
    wcagLevel: 'A',
    autoFix: 'Provide buttons for pinch-to-zoom, two-finger swipe actions'
  },
  labelInName: {
    check: 'Accessible name includes visible label text',
    severity: 'Medium',
    wcagLevel: 'A',
    autoFix: 'Ensure aria-label contains the visible button/link text'
  }
};
\`\`\`

---

### Principle 3: Understandable
Information and operation of user interface must be understandable.

#### 3.1 Readable (Level A, AA)
**Guidelines**:
- 3.1.1: Language of page identified
- 3.1.2: Language of parts identified (AA)

**Check for**:
\`\`\`javascript
const readableChecks = {
  htmlLang: {
    check: '<html> element has lang attribute',
    pattern: /<html(?![^>]*lang=)/gi,
    severity: 'Critical',
    wcagLevel: 'A',
    autoFix: 'Add lang="en" to <html> element'
  },
  langChanges: {
    check: 'Content in different language has lang attribute',
    severity: 'Medium',
    wcagLevel: 'AA',
    autoFix: 'Add lang="es" to Spanish content, lang="fr" to French content'
  }
};
\`\`\`

#### 3.2 Predictable (Level A, AA)
**Guidelines**:
- 3.2.1: On focus does not cause context change
- 3.2.2: On input does not cause context change
- 3.2.3: Consistent navigation (AA)
- 3.2.4: Consistent identification (AA)

**Check for**:
\`\`\`javascript
const predictableChecks = {
  autoSubmit: {
    check: 'Forms do not auto-submit on input',
    pattern: /<(?:select|input)[^>]*onChange=["'][^"']*submit/gi,
    severity: 'High',
    wcagLevel: 'A',
    autoFix: 'Add explicit submit button instead of auto-submitting onChange'
  },
  consistentNav: {
    check: 'Navigation is consistent across pages',
    severity: 'Medium',
    wcagLevel: 'AA',
    autoFix: 'Keep navigation order and labels consistent site-wide'
  },
  newWindow: {
    check: 'Links opening new windows warn users',
    pattern: /<a[^>]*target=["']_blank["'](?![^>]*(?:aria-label|title).*new window)/gi,
    severity: 'Medium',
    wcagLevel: 'AAA',
    autoFix: 'Add "(opens in new window)" to link text or aria-label'
  }
};
\`\`\`

#### 3.3 Input Assistance (Level A, AA)
**Guidelines**:
- 3.3.1: Error identification
- 3.3.2: Labels or instructions provided
- 3.3.3: Error suggestion (AA)
- 3.3.4: Error prevention for legal/financial (AA)

**Check for**:
\`\`\`javascript
const inputAssistanceChecks = {
  requiredFields: {
    check: 'Required fields marked with aria-required or required attribute',
    pattern: /<input(?![^>]*(?:required|aria-required))[^>]*>/gi,
    severity: 'High',
    wcagLevel: 'A',
    autoFix: 'Add required or aria-required="true" to required inputs'
  },
  errorMessages: {
    check: 'Form errors are clearly identified and described',
    severity: 'High',
    wcagLevel: 'A',
    autoFix: 'Link errors to form fields using aria-describedby, provide specific error messages'
  },
  instructions: {
    check: 'Complex inputs have instructions',
    severity: 'Medium',
    wcagLevel: 'A',
    autoFix: 'Add helper text for date formats, password requirements, etc.'
  },
  errorSuggestions: {
    check: 'Errors include suggestions for correction',
    severity: 'Medium',
    wcagLevel: 'AA',
    autoFix: 'Provide helpful error messages: "Email must include @" instead of "Invalid email"'
  }
};
\`\`\`

---

### Principle 4: Robust
Content must be robust enough to work with assistive technologies.

#### 4.1 Compatible (Level A, AA)
**Guidelines**:
- 4.1.2: Name, role, value programmatically determined
- 4.1.3: Status messages (AA)

**Check for**:
\`\`\`javascript
const robustChecks = {
  ariaRoles: {
    check: 'ARIA roles are valid',
    validRoles: ['alert', 'button', 'checkbox', 'dialog', 'link', 'menu', 'menuitem', 'navigation', 'radio', 'tab', 'tabpanel', 'textbox'],
    severity: 'High',
    wcagLevel: 'A',
    autoFix: 'Use valid ARIA roles from WAI-ARIA specification'
  },
  ariaAttributes: {
    check: 'ARIA attributes are valid for role',
    severity: 'High',
    wcagLevel: 'A',
    autoFix: 'Ensure aria-* attributes are appropriate for element role'
  },
  liveRegions: {
    check: 'Dynamic content updates announced to screen readers',
    severity: 'Medium',
    wcagLevel: 'AA',
    autoFix: 'Add aria-live="polite" for status messages, aria-live="assertive" for alerts'
  },
  formValidation: {
    check: 'Form validation messages use aria-invalid and aria-describedby',
    severity: 'High',
    wcagLevel: 'A',
    autoFix: 'Add aria-invalid="true" and aria-describedby="error-id" to invalid inputs'
  },
  customControls: {
    check: 'Custom UI controls have proper ARIA roles and states',
    examples: [
      { control: 'Custom checkbox', fix: 'role="checkbox" aria-checked="true/false"' },
      { control: 'Custom dropdown', fix: 'role="combobox" aria-expanded="true/false"' },
      { control: 'Custom tabs', fix: 'role="tablist" with role="tab" and role="tabpanel"' }
    ],
    severity: 'Critical',
    wcagLevel: 'A'
  }
};
\`\`\`

## 3. Run Automated Testing Tools

Integrate with automated accessibility testing:

\`\`\`javascript
const automatedTests = {
  axeCore: {
    tool: 'axe-core (Deque Systems)',
    install: 'npm install --save-dev axe-core',
    usage: \`
      import { axe } from 'axe-core';
      const results = await axe.run(document);
      return results.violations;
    \`,
    coverage: 'Catches ~57% of WCAG issues automatically'
  },
  lighthouse: {
    tool: 'Google Lighthouse Accessibility Audit',
    usage: 'lighthouse <url> --only-categories=accessibility --output json',
    coverage: 'Catches ~40% of WCAG issues, provides score 0-100'
  },
  pa11y: {
    tool: 'Pa11y',
    install: 'npm install --save-dev pa11y',
    usage: 'pa11y <url> --standard WCAG2AA',
    coverage: 'HTML_CodeSniffer-based testing'
  }
};
\`\`\`

## 4. Calculate Accessibility Score

\`\`\`javascript
function calculateAccessibilityScore(findings) {
  let score = 100;

  findings.forEach(issue => {
    // Deduct points based on severity
    const deductions = {
      'Critical': 10,  // Blocks basic access
      'High': 5,       // Significantly impairs access
      'Medium': 2,     // Moderately impairs access
      'Low': 1         // Minor inconvenience
    };

    score -= deductions[issue.severity] || 0;
  });

  // Floor at 0
  return Math.max(0, score);
}

function getComplianceLevel(score, findings) {
  const levelAIssues = findings.filter(f => f.wcagLevel === 'A').length;
  const levelAAIssues = findings.filter(f => f.wcagLevel === 'AA').length;
  const levelAAAIssues = findings.filter(f => f.wcagLevel === 'AAA').length;

  if (levelAIssues === 0 && levelAAIssues === 0 && levelAAAIssues === 0) {
    return 'AAA - Full Compliance';
  } else if (levelAIssues === 0 && levelAAIssues === 0) {
    return 'AA - Compliant';
  } else if (levelAIssues === 0) {
    return 'A - Minimum Compliance';
  } else {
    return 'Non-Compliant';
  }
}
\`\`\`

## 5. Generate Audit Report

\`\`\`markdown
# Accessibility Audit Report

**Date**: \${new Date().toISOString().split('T')[0]}
**Target**: \${URL || 'Local Codebase'}
**WCAG Level**: \${LEVEL || 'AA'}
**Compliance**: \${COMPLIANCE_LEVEL}

---

## 🎯 Overall Score: \${SCORE}/100

\${SCORE >= 90 ? '✅ Excellent' : SCORE >= 80 ? '🟢 Good' : SCORE >= 70 ? '🟡 Fair' : SCORE >= 60 ? '🟠 Poor' : '🔴 Critical Issues'}

**Target for Production**: >80/100 (AA compliance)

---

## 📊 Summary by Severity

| Severity | Count | Impact |
|----------|-------|--------|
| 🔴 Critical | \${CRITICAL_COUNT} | Blocks access for assistive technology users |
| 🟠 High | \${HIGH_COUNT} | Significantly impairs user experience |
| 🟡 Medium | \${MEDIUM_COUNT} | Moderately impairs user experience |
| 🔵 Low | \${LOW_COUNT} | Minor accessibility improvements |

**Total Issues**: \${TOTAL_ISSUES}

---

## 🎨 Summary by WCAG Principle

### 1. Perceivable (\${PERCEIVABLE_SCORE}/100)
- \${PERCEIVABLE_ISSUES_COUNT} issues found
- Key issues: \${TOP_PERCEIVABLE_ISSUES}

### 2. Operable (\${OPERABLE_SCORE}/100)
- \${OPERABLE_ISSUES_COUNT} issues found
- Key issues: \${TOP_OPERABLE_ISSUES}

### 3. Understandable (\${UNDERSTANDABLE_SCORE}/100)
- \${UNDERSTANDABLE_ISSUES_COUNT} issues found
- Key issues: \${TOP_UNDERSTANDABLE_ISSUES}

### 4. Robust (\${ROBUST_SCORE}/100)
- \${ROBUST_ISSUES_COUNT} issues found
- Key issues: \${TOP_ROBUST_ISSUES}

---

## 🔍 Detailed Findings

\${findings.map(issue => \`
### \${issue.severity === 'Critical' ? '🔴' : issue.severity === 'High' ? '🟠' : issue.severity === 'Medium' ? '🟡' : '🔵'} \${issue.title}

**WCAG**: \${issue.wcagGuideline} (Level \${issue.wcagLevel})
**Severity**: \${issue.severity}
**Impact**: \${issue.impact}

**Issue**:
\${issue.description}

**Location**:
\\\`\\\`\\\`
\${issue.location}
\\\`\\\`\\\`

**How to Fix**:
\${issue.fix}

**Code Example**:
\\\`\\\`\\\`html
<!-- ❌ Before -->
\${issue.exampleBefore}

<!-- ✅ After -->
\${issue.exampleAfter}
\\\`\\\`\\\`

---
\`).join('\\n')}

---

## 🚀 Quick Wins (Fix in <1 hour)

\${quickWins.map((fix, i) => \`
### \${i + 1}. \${fix.title}
- **Impact**: Fixes \${fix.issueCount} issue(s)
- **Time**: ~\${fix.estimatedMinutes} minutes
- **Action**: \${fix.action}
\`).join('\\n')}

---

## 📋 Remediation Roadmap

### Phase 1: Critical Issues (Week 1)
\${criticalIssues.map(issue => \`- [ ] \${issue.title}\`).join('\\n')}

### Phase 2: High Priority (Week 2)
\${highIssues.map(issue => \`- [ ] \${issue.title}\`).join('\\n')}

### Phase 3: Medium Priority (Week 3-4)
\${mediumIssues.map(issue => \`- [ ] \${issue.title}\`).join('\\n')}

### Phase 4: Low Priority (Ongoing)
\${lowIssues.map(issue => \`- [ ] \${issue.title}\`).join('\\n')}

---

## 🧪 Testing Recommendations

1. **Automated Testing**
   - Install: \`npm install --save-dev axe-core @axe-core/react\`
   - Add to CI/CD: \`npm run test:a11y\`
   - Target: 0 critical violations

2. **Manual Testing**
   - Keyboard navigation (no mouse)
   - Screen reader testing (NVDA, JAWS, VoiceOver)
   - Zoom to 200% (text readability)
   - Color blindness simulation

3. **User Testing**
   - Test with users who use assistive technologies
   - Document pain points and confusion
   - Iterate based on feedback

---

## 📚 Resources

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [WCAG 2.2 Guidelines](https://www.w3.org/WAI/WCAG22/quickref/)
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
- [axe DevTools Browser Extension](https://www.deque.com/axe/devtools/)

---

**Next Steps**:
1. Fix all critical issues immediately
2. Run \`/accessibility/fix\` for automated fixes
3. Run \`/accessibility/test\` for validation
4. Schedule regular audits (monthly recommended)

---

**Generated**: \${new Date().toLocaleString()}
**Audit Tool**: Claude Code - Accessibility Auditor
\`\`\`

Save report to: accessibility-audits/audit-\${new Date().toISOString().split('T')[0]}.md
  `
})
```

## Usage Examples

```bash
# Audit current codebase for WCAG AA compliance
/accessibility/audit

# Audit remote URL
/accessibility/audit --url https://example.com

# Audit for AAA compliance (stricter)
/accessibility/audit --level AAA

# Generate JSON report for CI/CD integration
/accessibility/audit --format json > accessibility-report.json

# Audit specific compliance level
/accessibility/audit --url https://myapp.com --level AA --format markdown
```

## Output Includes

1. **Overall Score** (0-100)
2. **Compliance Level** (A, AA, AAA, or Non-Compliant)
3. **Issues by Severity** (Critical, High, Medium, Low)
4. **Issues by WCAG Principle** (Perceivable, Operable, Understandable, Robust)
5. **Detailed Findings** with code examples
6. **Quick Wins** (<1 hour fixes)
7. **Remediation Roadmap** (4-phase plan)
8. **Testing Recommendations**

## Success Criteria

- ✓ Score >80/100 for production deployment
- ✓ 0 critical accessibility violations
- ✓ WCAG AA compliance achieved (for Level AA target)
- ✓ All automated test issues resolved
- ✓ Manual testing with assistive technologies passes

## When to Use

- **Pre-Launch**: Before deploying new features or pages
- **Regular Audits**: Monthly accessibility checks
- **Compliance**: Legal requirement verification (ADA, Section 508)
- **Improvements**: Identify and prioritize accessibility work
- **CI/CD Integration**: Automated accessibility gates

## Business Impact

**ROI**: $45,000/year

- **Legal Compliance**: Avoid ADA lawsuits ($20,000/year in risk mitigation)
- **Market Reach**: +15% addressable market (people with disabilities) ($15,000/year)
- **SEO Benefits**: Better search rankings ($5,000/year)
- **User Experience**: Improved UX for all users ($5,000/year)

---

**Next Commands**: `/accessibility/fix` (automated fixes), `/accessibility/test` (validation)
**Review Frequency**: Monthly recommended, or before major releases
