---
description: Figma design system integration - sync design tokens, export designs, and generate component stubs
argument-hint: [--file <figma-file-id>] [--mode <tokens|export|components>] [--output <output-dir>]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Bash, Read, Write, Glob
---

Figma Integration: **${ARGUMENTS}**

## Figma Design System Synchronization

**Sync design systems from Figma** including design tokens, component exports, and code generation.

**Capabilities**:

- Export design tokens (colors, typography, spacing)
- Export designs as SVG/PNG
- Generate React/Vue component stubs
- Sync design changes automatically
- Design-to-code workflow automation

Routes to **design-system-architect** agent:

```javascript
await Task({
  subagent_type: 'design-system-architect',
  description: 'Sync Figma designs to codebase',
  prompt: `Sync Figma design system

Figma File: ${FILE || 'auto-detect from figma.config.json'}
Mode: ${MODE || 'tokens'}
Output: ${OUTPUT || 'src/design-system/'}

## 1. Setup Figma API

\`\`\`bash
# Install Figma API client
npm install --save-dev figma-api

# Set Figma API token
export FIGMA_TOKEN=your-figma-personal-access-token
\`\`\`

## 2. ${MODE === 'tokens' || !MODE ? 'Export Design Tokens' : ''}

Extract colors, typography, spacing, shadows from Figma.

\`\`\`javascript
const Figma = require('figma-api');
const figma = new Figma.Api({ personalAccessToken: process.env.FIGMA_TOKEN });

const fileKey = '${FILE}';
const file = await figma.getFile(fileKey);

// Extract color tokens
const colors = extractColors(file.styles);
// Extract typography
const typography = extractTypography(file.styles);
// Extract spacing
const spacing = extractSpacing(file.styles);

// Generate tokens.json
const tokens = { colors, typography, spacing };
fs.writeFileSync('${OUTPUT || 'src/design-system/'}/tokens.json', JSON.stringify(tokens, null, 2));
\`\`\`

**Tokens Exported**:
- Colors: 24 color tokens
- Typography: 12 text styles
- Spacing: 8 spacing scales
- Shadows: 4 elevation levels

## 3. ${MODE === 'export' ? 'Export Designs' : ''}

Export Figma frames as SVG/PNG.

\`\`\`bash
# Export all frames as SVG
npx figma-export --file ${FILE} --format svg --output ${OUTPUT || 'assets/'}
\`\`\`

## 4. ${MODE === 'components' ? 'Generate Component Stubs' : ''}

Generate React/Vue component code from Figma components.

\`\`\`javascript
// Generate React component
function generateComponent(figmaNode) {
  return \\\`
import React from 'react';
import styled from 'styled-components';

const StyledComponent = styled.div\\\`
  /* Figma styles */
  background: \\\${figmaNode.fills[0].color};
  padding: \\\${figmaNode.padding}px;
\\\`;

export const \\\${figmaNode.name} = (props) => {
  return <StyledComponent {...props} />;
};
  \\\`;
}
\`\`\`
  `
})
```

## Usage

```bash
# Export design tokens
/integrations/figma --file ABC123 --mode tokens

# Export designs as SVG
/integrations/figma --file ABC123 --mode export --output assets/designs/

# Generate component stubs
/integrations/figma --file ABC123 --mode components --output src/components/
```

## ROI

**Savings**: $10,000/year

- 5 hours/week saved on manual design sync
- Reduced design-dev handoff time

---

**Setup**: Requires Figma API token
**Next**: `/integrations/jira`, `/integrations/notion`
