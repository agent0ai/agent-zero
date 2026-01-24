---
description: Automated accessibility fixes for common WCAG violations with code transformations
argument-hint: [--audit-report <path>] [--auto-apply] [--severity <critical|high|medium|low>]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Read, Glob, Grep, Edit, Write
---

Accessibility Fix: **${ARGUMENTS}**

## Automated Accessibility Remediation

**Automatically fix common accessibility issues** identified by `/accessibility/audit`.

**Capabilities**:

- Fix missing alt attributes on images
- Add ARIA labels to icon-only buttons
- Correct heading hierarchy
- Add form labels and associations
- Fix color contrast issues
- Add keyboard navigation support
- Fix ARIA roles and attributes
- Add language attributes
- Fix focus indicators

Routes to **accessibility-auditor** agent:

```javascript
await Task({
  subagent_type: 'accessibility-auditor',
  description: 'Apply automated accessibility fixes',
  prompt: `Apply automated accessibility fixes to codebase

Audit Report: ${AUDIT_REPORT || 'Run fresh audit first'}
Auto-Apply: ${AUTO_APPLY ? 'Yes - apply fixes automatically' : 'No - generate fix preview'}
Severity Filter: ${SEVERITY || 'all'} (only fix issues at this severity or higher)

Execute automated accessibility remediation:

## 1. Load Audit Report

${AUDIT_REPORT ? \`
### Use Existing Audit Report
- Read audit report from: \${AUDIT_REPORT}
- Extract all fixable issues
- Filter by severity: \${SEVERITY || 'all'}
\` : \`
### Run Fresh Audit
- Execute /accessibility/audit first
- Use latest audit results
- Identify all auto-fixable issues
\`}

## 2. Categorize Auto-Fixable Issues

\`\`\`javascript
const autoFixablePatterns = {
  // === CRITICAL FIXES ===

  missingAltText: {
    severity: 'Critical',
    wcag: '1.1.1 (Level A)',
    pattern: /<img([^>]*)(?!alt=)([^>]*)>/gi,
    fix: (match) => {
      // Check if image is decorative or meaningful
      const src = match.match(/src=["']([^"']+)["']/)?.[1] || '';
      const filename = src.split('/').pop()?.split('.')[0] || '';

      // If clearly decorative (icon, spacer, bullet)
      if (/(?:icon|spacer|bullet|divider|bg|background)/i.test(filename)) {
        return match.replace('<img', '<img alt=""');
      }

      // Otherwise, generate descriptive alt from filename
      const altText = filename
        .replace(/[-_]/g, ' ')
        .replace(/\\b\\w/g, l => l.toUpperCase());

      return match.replace('<img', \`<img alt="\${altText}"\`);
    },
    description: 'Add alt attributes to images',
    autoFixable: true
  },

  iconOnlyButtons: {
    severity: 'Critical',
    wcag: '4.1.2 (Level A)',
    pattern: /<button([^>]*)>\\s*<(?:i|svg|span class=["'][^"']*icon)([^>]*)>(?:<\\/[^>]+>)?\\s*<\\/button>/gi,
    fix: (match) => {
      // Extract icon class or SVG to infer purpose
      const iconMatch = match.match(/class=["']([^"']*(?:fa-|icon-|material-icons)([^"']*))/);
      const iconName = iconMatch?.[2]?.replace(/fa-|icon-|material-icons-/g, '').trim() || 'action';

      // Generate aria-label from icon name
      const ariaLabel = iconName
        .replace(/[-_]/g, ' ')
        .replace(/\\b\\w/g, l => l.toUpperCase());

      return match.replace('<button', \`<button aria-label="\${ariaLabel}"\`);
    },
    description: 'Add aria-label to icon-only buttons',
    autoFixable: true
  },

  missingFormLabels: {
    severity: 'Critical',
    wcag: '3.3.2 (Level A)',
    pattern: /<input(?![^>]*(?:aria-label=|id=["'][^"']*["'][^>]*>\\s*<label[^>]*for=))([^>]*name=["']([^"']+)["'][^>]*)>/gi,
    fix: (match, attributes, name) => {
      // Generate label text from input name
      const labelText = name
        .replace(/[-_]/g, ' ')
        .replace(/\\b\\w/g, l => l.toUpperCase());

      const inputId = name.toLowerCase().replace(/[^a-z0-9]/g, '-');

      return \`<label for="\${inputId}">\${labelText}</label>
<input\${attributes} id="\${inputId}">\`;
    },
    description: 'Add labels to form inputs',
    autoFixable: true
  },

  missingLangAttribute: {
    severity: 'Critical',
    wcag: '3.1.1 (Level A)',
    pattern: /<html(?![^>]*lang=)/gi,
    fix: (match) => {
      return match.replace('<html', '<html lang="en"');
    },
    description: 'Add lang attribute to <html>',
    autoFixable: true
  },

  // === HIGH PRIORITY FIXES ===

  outlineNone: {
    severity: 'High',
    wcag: '2.4.7 (Level AA)',
    pattern: /([^{}]*{[^}]*)(outline:\\s*(?:none|0)\\s*;?)([^}]*})/gi,
    fix: (match, before, outlineRule, after) => {
      // Replace outline: none with visible focus style
      const replacement = \`
  outline: 2px solid #0066CC;
  outline-offset: 2px;\`;

      return \`\${before}\${replacement}\${after}\`;
    },
    description: 'Replace outline: none with visible focus indicators',
    autoFixable: true,
    fileTypes: ['.css', '.scss', '.less', '.styled.js', '.styled.ts']
  },

  divWithOnClick: {
    severity: 'High',
    wcag: '2.1.1 (Level A)',
    pattern: /<div([^>]*onClick=)([^>]*)>/gi,
    fix: (match, onClickAttr, restAttrs) => {
      // Convert div onClick to button
      // Preserve all attributes except onClick (we'll add keyboard handler)
      return \`<button\${restAttrs} type="button" \${onClickAttr} onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') \${onClickAttr.match(/=\\{([^}]+)\\}/)?.[1] || onClickAttr.match(/="([^"]+)"/)?.[1]}() }}>\`;
    },
    description: 'Convert <div onClick> to <button> with keyboard support',
    autoFixable: true,
    note: 'May require manual style adjustments'
  },

  interactiveWithoutTabIndex: {
    severity: 'High',
    wcag: '2.1.1 (Level A)',
    pattern: /<div([^>]*role=["'](?:button|link|tab)["'](?![^>]*tabindex=))([^>]*)>/gi,
    fix: (match, roleAttr, restAttrs) => {
      return \`<div\${roleAttr}\${restAttrs} tabindex="0">\`;
    },
    description: 'Add tabindex="0" to interactive elements',
    autoFixable: true
  },

  // === MEDIUM PRIORITY FIXES ===

  missingAutocomplete: {
    severity: 'Medium',
    wcag: '1.3.5 (Level AA)',
    patterns: [
      {
        field: 'email',
        pattern: /<input([^>]*type=["']email["'](?![^>]*autocomplete=))([^>]*)>/gi,
        autocomplete: 'email'
      },
      {
        field: 'name',
        pattern: /<input([^>]*(?:name|id)=["'][^"']*name[^"']*["'](?![^>]*autocomplete=))([^>]*)>/gi,
        autocomplete: 'name'
      },
      {
        field: 'tel',
        pattern: /<input([^>]*type=["']tel["'](?![^>]*autocomplete=))([^>]*)>/gi,
        autocomplete: 'tel'
      },
      {
        field: 'street-address',
        pattern: /<input([^>]*(?:name|id)=["'][^"']*(?:address|street)[^"']*["'](?![^>]*autocomplete=))([^>]*)>/gi,
        autocomplete: 'street-address'
      }
    ],
    fix: (pattern) => (match, attr1, attr2) => {
      return \`<input\${attr1}\${attr2} autocomplete="\${pattern.autocomplete}">\`;
    },
    description: 'Add autocomplete attributes to form fields',
    autoFixable: true
  },

  headingHierarchySkip: {
    severity: 'Medium',
    wcag: '1.3.1 (Level A)',
    detect: (content) => {
      // Extract all headings in order
      const headings = [];
      const headingRegex = /<h([1-6])[^>]*>([^<]*)<\\/h[1-6]>/gi;
      let match;

      while ((match = headingRegex.exec(content)) !== null) {
        headings.push({
          level: parseInt(match[1]),
          text: match[2],
          position: match.index,
          fullMatch: match[0]
        });
      }

      // Find hierarchy skips (e.g., h1 → h3, skipping h2)
      const issues = [];
      for (let i = 1; i < headings.length; i++) {
        const prevLevel = headings[i - 1].level;
        const currLevel = headings[i].level;

        if (currLevel > prevLevel + 1) {
          issues.push({
            heading: headings[i],
            expectedLevel: prevLevel + 1,
            actualLevel: currLevel,
            fix: headings[i].fullMatch.replace(\`<h\${currLevel}\`, \`<h\${prevLevel + 1}\`)
          });
        }
      }

      return issues;
    },
    description: 'Fix heading hierarchy (no level skipping)',
    autoFixable: true,
    note: 'Review semantic meaning after fix'
  },

  linkTextNotDescriptive: {
    severity: 'Medium',
    wcag: '2.4.4 (Level A)',
    pattern: /<a([^>]*)>\\s*(click here|here|read more|more|link)\\s*<\\/a>/gi,
    fix: (match, attributes) => {
      // Extract href to generate better link text
      const href = attributes.match(/href=["']([^"']+)["']/)?.[1] || '';
      const pageName = href.split('/').filter(Boolean).pop()?.replace(/[-_]/g, ' ') || 'this page';

      return \`<a\${attributes}>Read more about \${pageName}</a>\`;
    },
    description: 'Improve non-descriptive link text',
    autoFixable: true,
    note: 'Review generated text for accuracy'
  },

  // === LOW PRIORITY FIXES ===

  targetBlankWithoutWarning: {
    severity: 'Low',
    wcag: '3.2.4 (Level AAA)',
    pattern: /<a([^>]*target=["']_blank["'](?![^>]*(?:aria-label|title).*new window))([^>]*)>([^<]*)<\\/a>/gi,
    fix: (match, attr1, attr2, linkText) => {
      return \`<a\${attr1}\${attr2} aria-label="\${linkText} (opens in new window)">\${linkText}</a>\`;
    },
    description: 'Add "opens in new window" warning to target="_blank" links',
    autoFixable: true
  },

  svgWithoutTitle: {
    severity: 'Low',
    wcag: '1.1.1 (Level A)',
    pattern: /<svg(?![^>]*(?:aria-label=|role="img"|<title>))([^>]*)>([^<]*(?:(?!<title>)<[^<]*)*)<\\/svg>/gi,
    fix: (match, attributes, content) => {
      // Generate title from SVG content or filename
      const titleText = 'Graphic';
      return \`<svg\${attributes} role="img" aria-label="\${titleText}">
  <title>\${titleText}</title>
  \${content}
</svg>\`;
    },
    description: 'Add title or aria-label to SVG elements',
    autoFixable: true,
    note: 'Update title text to describe graphic'
  }
};
\`\`\`

## 3. Scan Codebase for Issues

\`\`\`javascript
// Find all web-accessible files
const webFiles = await Glob({
  patterns: [
    '**/*.html',
    '**/*.jsx',
    '**/*.tsx',
    '**/*.vue',
    '**/*.svelte',
    'src/components/**/*',
    'src/pages/**/*'
  ]
});

// Scan each file for fixable issues
const fixableIssues = [];

for (const file of webFiles) {
  const content = await Read({ file_path: file });

  // Check each auto-fixable pattern
  for (const [issueKey, pattern] of Object.entries(autoFixablePatterns)) {
    // ... pattern matching logic
    if (matches) {
      fixableIssues.push({
        file,
        issue: issueKey,
        severity: pattern.severity,
        wcag: pattern.wcag,
        matches,
        fix: pattern.fix
      });
    }
  }
}
\`\`\`

## 4. Apply Fixes or Generate Preview

${AUTO_APPLY ? \`
### Auto-Apply Mode: Apply Fixes Automatically

\`\`\`javascript
const appliedFixes = [];

for (const issue of fixableIssues) {
  const content = await Read({ file_path: issue.file });
  let updatedContent = content;

  // Apply all fixes for this pattern
  for (const match of issue.matches) {
    const fixedCode = issue.fix(match);
    updatedContent = updatedContent.replace(match, fixedCode);
  }

  // Write updated file
  await Edit({
    file_path: issue.file,
    old_string: content,
    new_string: updatedContent
  });

  appliedFixes.push({
    file: issue.file,
    issue: issue.issue,
    count: issue.matches.length
  });
}
\`\`\`

\` : \`
### Preview Mode: Generate Fix Preview

\`\`\`javascript
// Generate preview of all fixes without applying
const fixPreview = fixableIssues.map(issue => ({
  file: issue.file,
  issue: issue.issue,
  severity: issue.severity,
  wcag: issue.wcag,
  matchCount: issue.matches.length,
  examples: issue.matches.slice(0, 2).map(match => ({
    before: match,
    after: issue.fix(match)
  }))
}));
\`\`\`
\`}

## 5. Generate Fix Report

\`\`\`markdown
# Accessibility Fixes Applied

**Date**: \${new Date().toISOString().split('T')[0]}
**Mode**: ${AUTO_APPLY ? '✅ Auto-Apply' : '👁️ Preview Only'}
**Severity Filter**: \${SEVERITY || 'All'}

---

## 📊 Summary

${AUTO_APPLY ? \`
**Fixes Applied**: \${TOTAL_FIXES}
**Files Modified**: \${FILES_MODIFIED}
**Issues Resolved**: \${ISSUES_RESOLVED}
\` : \`
**Fixable Issues Found**: \${TOTAL_FIXABLE}
**Files Affected**: \${FILES_AFFECTED}
**Potential Improvements**: \${POTENTIAL_IMPROVEMENTS}
\`}

---

## 🔧 Fixes by Severity

| Severity | Fixes ${AUTO_APPLY ? 'Applied' : 'Available'} | Files Affected |
|----------|------|----------------|
| 🔴 Critical | \${CRITICAL_FIXES} | \${CRITICAL_FILES} |
| 🟠 High | \${HIGH_FIXES} | \${HIGH_FILES} |
| 🟡 Medium | \${MEDIUM_FIXES} | \${MEDIUM_FILES} |
| 🔵 Low | \${LOW_FIXES} | \${LOW_FILES} |

---

## 📝 Detailed Fixes

\${fixes.map(fix => \`
### \${fix.file}

**Issue**: \${fix.issue} (\${fix.severity})
**WCAG**: \${fix.wcag}
**Occurrences**: \${fix.count}

${AUTO_APPLY ? \`
✅ **Applied** - \${fix.count} fix(es) applied automatically

\` : \`
**Examples**:

#### Before:
\\\`\\\`\\\`html
\${fix.examples[0].before}
\\\`\\\`\\\`

#### After:
\\\`\\\`\\\`html
\${fix.examples[0].after}
\\\`\\\`\\\`

\`}

---
\`).join('\\n')}

---

${AUTO_APPLY ? \`
## ✅ Next Steps

1. **Review Changes**
   \\\`\\\`\\\`bash
   git diff
   \\\`\\\`\\\`

2. **Test Fixes**
   \\\`\\\`\\\`bash
   /accessibility/test
   \\\`\\\`\\\`

3. **Verify Improvements**
   \\\`\\\`\\\`bash
   /accessibility/audit
   \\\`\\\`\\\`
   Expected score improvement: +\${EXPECTED_SCORE_IMPROVEMENT} points

4. **Commit Changes**
   \\\`\\\`\\\`bash
   git add .
   git commit -m "fix(a11y): Apply automated accessibility fixes

   - Fix \${CRITICAL_FIXES} critical issues
   - Fix \${HIGH_FIXES} high-priority issues
   - Improve WCAG compliance

   🤖 Generated with Claude Code
   Co-Authored-By: Claude <noreply@anthropic.com>"
   \\\`\\\`\\\`

\` : \`
## 🚀 Apply Fixes

To apply these fixes automatically:

\\\`\\\`\\\`bash
/accessibility/fix --auto-apply

# Or apply only critical issues:
/accessibility/fix --auto-apply --severity critical

# Or apply from specific audit report:
/accessibility/fix --audit-report accessibility-audits/audit-2024-11-15.md --auto-apply
\\\`\\\`\\\`

\`}

---

## ⚠️ Manual Review Required

Some issues cannot be auto-fixed and require manual intervention:

\${manualReviewIssues.map(issue => \`
### \${issue.title}
**Severity**: \${issue.severity}
**WCAG**: \${issue.wcag}
**Why Manual**: \${issue.reason}

**Action Required**:
\${issue.action}

**Location**: \${issue.file}:\${issue.line}
\`).join('\\n')}

---

## 📊 Expected Impact

${AUTO_APPLY ? \`
**Before Fixes**:
- Accessibility Score: \${BEFORE_SCORE}/100
- Critical Issues: \${BEFORE_CRITICAL}
- Total Issues: \${BEFORE_TOTAL}

**After Fixes**:
- Accessibility Score: \${AFTER_SCORE}/100 (+\${SCORE_IMPROVEMENT})
- Critical Issues: \${AFTER_CRITICAL} (-\${CRITICAL_REDUCTION})
- Total Issues: \${AFTER_TOTAL} (-\${TOTAL_REDUCTION})

**Improvement**: \${PERCENT_IMPROVEMENT}% reduction in accessibility issues

\` : \`
**If Applied**:
- Expected Score Improvement: +\${EXPECTED_SCORE_IMPROVEMENT} points
- Critical Issues Resolved: \${CRITICAL_FIXES}
- Total Issues Resolved: \${TOTAL_FIXES}
- Estimated Time to Apply Manually: ~\${MANUAL_TIME_HOURS} hours
- Estimated Time to Apply Automatically: ~\${AUTO_TIME_MINUTES} minutes

**ROI**: Save \${MANUAL_TIME_HOURS} hours of manual fixing

\`}

---

**Generated**: \${new Date().toLocaleString()}
**Fix Tool**: Claude Code - Accessibility Auditor
\`\`\`

Save report to: accessibility-fixes/fixes-\${new Date().toISOString().split('T')[0]}.md
  `
})
```

## Usage Examples

```bash
# Preview available fixes without applying
/accessibility/fix

# Auto-apply all fixable issues
/accessibility/fix --auto-apply

# Fix only critical issues
/accessibility/fix --auto-apply --severity critical

# Fix high and critical issues
/accessibility/fix --auto-apply --severity high

# Use specific audit report
/accessibility/fix --audit-report accessibility-audits/audit-2024-11-15.md --auto-apply

# Preview fixes for specific severity
/accessibility/fix --severity critical
```

## Auto-Fixable Issues

### Critical (Auto-Fixable)

- ✅ Missing alt text on images
- ✅ Icon-only buttons without aria-label
- ✅ Form inputs without labels
- ✅ Missing lang attribute on <html>

### High Priority (Auto-Fixable)

- ✅ outline: none without replacement
- ✅ <div onClick> without keyboard support
- ✅ Interactive elements without tabindex

### Medium Priority (Auto-Fixable)

- ✅ Missing autocomplete on form fields
- ✅ Heading hierarchy skips
- ✅ Non-descriptive link text

### Low Priority (Auto-Fixable)

- ✅ target="_blank" without warning
- ✅ SVGs without title or aria-label

## Manual Review Required

Some issues need human judgment:

- Color contrast adjustments (requires design decisions)
- Complex ARIA patterns (requires understanding of widget behavior)
- Custom keyboard navigation (requires interaction design)
- Screen reader text optimization (requires content expertise)

## Success Criteria

- ✓ All auto-fixable critical issues resolved
- ✓ Accessibility score improved by 15-30 points
- ✓ All fixes validated with /accessibility/test
- ✓ No new issues introduced by fixes

## When to Use

- **After Audit**: Apply fixes after running /accessibility/audit
- **Pre-Commit**: Fix issues before committing code
- **CI/CD Integration**: Auto-fix in development, preview in CI
- **Bulk Improvements**: Fix multiple files at once

## Safety Features

- **Preview Mode**: Default mode shows fixes without applying
- **Backup**: Always review git diff before committing
- **Validation**: Run /accessibility/test after applying fixes
- **Severity Filter**: Apply only critical/high fixes first

## Time Savings

**Manual Fixing**: 4-8 hours for typical codebase
**Automated Fixing**: 2-5 minutes

**ROI**: Save 4-8 hours per fix cycle

---

**Next Commands**: `/accessibility/test` (validate fixes), `/accessibility/audit` (verify improvement)
**Safety**: Always review changes with `git diff` before committing
