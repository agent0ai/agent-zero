---
description: Define design system colors and typography using Tailwind palette and Google Fonts
argument-hint: <product-name>
allowed-tools: Read, Write, Edit, AskUserQuestion, Bash
model: claude-sonnet-4-5
timeout: 900
retry: 2
cost_estimate: 0.08-0.12

# Validation
validation:
  input:
    product_name:
      schema: .claude/validation/schemas/common/spec-name.json
      required: true
      error_template: INVALID_SPEC_NAME

  output:
    schema: .claude/validation/schemas/design-os/design-tokens-output.json
    required_files:
      - 'design-os/${product_name}/design-tokens.json'
    min_file_size: 500
    quality_threshold: 0.9
    content_requirements:
      - "colors object with primary, secondary, neutral"
      - "typography object with fonts"
      - "spacing scale"
      - "breakpoints (mobile, tablet, desktop)"
      - "Tailwind CSS compliance"
      - "Google Fonts usage"

# Prerequisites
prerequisites:
  - command: /design-os/product-vision
    file_exists: 'design-os/${product_name}/vision.md'
    error_message: "Run /design-os/product-vision first to define product vision"

# Version
version: 2.0.0
changelog:
  - version: 2.0.0
    date: 2026-01-20
    changes:
      - "Migrated to modern pattern with comprehensive validation"
      - "Added input validation for product name"
      - "Added prerequisite check for vision.md"
      - "Added Tailwind CSS and Google Fonts compliance checks"
      - "Updated to design-os folder structure"
  - version: 1.0.0
    date: 2025-10-15
    changes:
      - "Initial implementation with Tailwind palette and Google Fonts"
---

# Design Tokens

Product name: **$ARGUMENTS**

## Step 1: Validate Input & Prerequisites

```bash
PRODUCT_NAME="$ARGUMENTS"

# Validate product name format
if [[ ! "$PRODUCT_NAME" =~ ^[a-z0-9-]+$ ]]; then
  echo "❌ ERROR: Invalid product name"
  echo ""
  echo "Product name must:"
  echo "  • Be lowercase"
  echo "  • Use only letters, numbers, and hyphens"
  echo "  • Example: 'my-product' or 'app-v2'"
  exit 1
fi

# Check prerequisite: vision.md must exist
VISION_FILE="design-os/$PRODUCT_NAME/vision.md"
if [ ! -f "$VISION_FILE" ]; then
  echo "❌ ERROR: Product vision not found"
  echo ""
  echo "Run this command first:"
  echo "  /design-os/product-vision $PRODUCT_NAME"
  exit 1
fi

echo "✓ Input validated: $PRODUCT_NAME"
echo "✓ Prerequisites met: vision.md exists"
```

## Step 2: Read Product Vision

```javascript
const PRODUCT_NAME = process.env.ARGUMENTS;
const visionContent = await Read({
  file_path: `design-os/${PRODUCT_NAME}/vision.md`
});

// Analyze product type and target audience to suggest appropriate style
```

## Step 3: Explain the Process

> "Now we'll establish the visual identity for **$ARGUMENTS**:
>
> - **Primary color** - Your brand's main color (from Tailwind palette)
> - **Secondary color** - Complementary accent color
> - **Neutral colors** - For text, backgrounds, borders
> - **Typography** - Heading, body, and monospace fonts (from Google Fonts)
> - **Spacing** - Consistent spacing scale
> - **Breakpoints** - Responsive design breakpoints
>
> These design tokens will be applied consistently across all screen designs to ensure visual coherence."

## Step 4: Color Selection

Present Tailwind color palette options organized by category:

### Warm Colors

- **Red** (red-50 to red-950) - Bold, energetic, urgent, error states
- **Orange** (orange-50 to orange-950) - Friendly, creative, warm, call-to-action
- **Amber** (amber-50 to amber-950) - Optimistic, attention-grabbing, warnings
- **Yellow** (yellow-50 to yellow-950) - Cheerful, highlighting, alerts

### Cool Colors

- **Green** (green-50 to green-950) - Growth, success, natural, confirmations
- **Emerald** (emerald-50 to emerald-950) - Premium, refreshing, eco-friendly
- **Teal** (teal-50 to teal-950) - Balanced, sophisticated, tech
- **Cyan** (cyan-50 to cyan-950) - Fresh, modern, clean, informational
- **Sky** (sky-50 to sky-950) - Open, trustworthy, calm
- **Blue** (blue-50 to blue-950) - Professional, reliable, corporate

### Purple Range

- **Indigo** (indigo-50 to indigo-950) - Creative, wise, premium
- **Violet** (violet-50 to violet-950) - Innovative, magical, futuristic
- **Purple** (purple-50 to purple-950) - Luxurious, creative, artistic
- **Fuchsia** (fuchsia-50 to fuchsia-950) - Bold, playful, vibrant
- **Pink** (pink-50 to pink-950) - Friendly, approachable, lifestyle
- **Rose** (rose-50 to rose-950) - Warm, romantic, elegant

### Neutrals (for backgrounds, text, borders)

- **Slate** (slate-50 to slate-950) - Cool gray, modern, professional
- **Gray** (gray-50 to gray-950) - Balanced, neutral, versatile
- **Zinc** (zinc-50 to zinc-950) - Cool, industrial, minimalist
- **Stone** (stone-50 to stone-950) - Warm gray, organic, natural

**Ask**: "Based on your product vision, what aesthetic are you going for - professional, playful, bold, minimal? I can suggest color pairings that match."

## Step 5: Typography Selection

Present Google Fonts options organized by style:

### Modern & Clean

**Heading**: DM Sans
**Body**: DM Sans
**Mono**: IBM Plex Mono
*Use for*: SaaS, dashboards, modern apps

### Professional

**Heading**: Inter
**Body**: Inter
**Mono**: JetBrains Mono
*Use for*: Business tools, corporate apps, documentation

### Friendly & Rounded

**Heading**: Outfit
**Body**: Outfit
**Mono**: Space Mono
*Use for*: Consumer apps, lifestyle products, creative tools

### Bold & Impactful

**Heading**: Plus Jakarta Sans
**Body**: Plus Jakarta Sans
**Mono**: Fira Code
*Use for*: Marketing sites, creative platforms, bold brands

### Classic & Elegant

**Heading**: Lora
**Body**: Source Sans Pro
**Mono**: Source Code Pro
*Use for*: Editorial, publishing, content-heavy sites

**Ask**: "Which typography style matches your brand personality? Or would you prefer to mix and match?"

## Step 6: Draft Design Tokens

Present the complete design tokens structure:

```json
{
  "colors": {
    "primary": {
      "50": "#...",
      "100": "#...",
      // ... (Tailwind scale)
      "900": "#...",
      "950": "#..."
    },
    "secondary": {
      "50": "#...",
      // ... (Tailwind scale)
    },
    "neutral": {
      "50": "#...",
      // ... (Tailwind scale for backgrounds, text, borders)
    },
    "semantic": {
      "success": "green-600",
      "warning": "amber-500",
      "error": "red-600",
      "info": "blue-600"
    }
  },
  "typography": {
    "fonts": {
      "heading": "DM Sans",
      "body": "DM Sans",
      "mono": "IBM Plex Mono"
    },
    "sizes": {
      "xs": "0.75rem",
      "sm": "0.875rem",
      "base": "1rem",
      "lg": "1.125rem",
      "xl": "1.25rem",
      "2xl": "1.5rem",
      "3xl": "1.875rem",
      "4xl": "2.25rem",
      "5xl": "3rem"
    },
    "weights": {
      "light": "300",
      "normal": "400",
      "medium": "500",
      "semibold": "600",
      "bold": "700"
    }
  },
  "spacing": {
    "0": "0",
    "1": "0.25rem",
    "2": "0.5rem",
    "3": "0.75rem",
    "4": "1rem",
    "6": "1.5rem",
    "8": "2rem",
    "12": "3rem",
    "16": "4rem",
    "24": "6rem"
  },
  "breakpoints": {
    "sm": "640px",
    "md": "768px",
    "lg": "1024px",
    "xl": "1280px",
    "2xl": "1536px"
  },
  "shadows": {
    "sm": "0 1px 2px 0 rgb(0 0 0 / 0.05)",
    "DEFAULT": "0 1px 3px 0 rgb(0 0 0 / 0.1)",
    "md": "0 4px 6px -1px rgb(0 0 0 / 0.1)",
    "lg": "0 10px 15px -3px rgb(0 0 0 / 0.1)",
    "xl": "0 20px 25px -5px rgb(0 0 0 / 0.1)"
  },
  "borderRadius": {
    "none": "0",
    "sm": "0.125rem",
    "DEFAULT": "0.25rem",
    "md": "0.375rem",
    "lg": "0.5rem",
    "xl": "0.75rem",
    "2xl": "1rem",
    "full": "9999px"
  }
}
```

**Ask**: "Does this design system feel right for your product? Would you like to adjust any colors, fonts, or other tokens?"

Iterate until approved.

## Step 7: Create Design Tokens File

```javascript
const PRODUCT_NAME = process.env.ARGUMENTS;
const tokensPath = `design-os/${PRODUCT_NAME}/design-tokens.json`;

await Write({
  file_path: tokensPath,
  content: JSON.stringify({
    colors: {
      primary: {
        // Full Tailwind scale for chosen primary color
      },
      secondary: {
        // Full Tailwind scale for chosen secondary color
      },
      neutral: {
        // Full Tailwind scale for chosen neutral
      },
      semantic: {
        success: "green-600",
        warning: "amber-500",
        error: "red-600",
        info: "blue-600"
      }
    },
    typography: {
      fonts: {
        heading: "[Chosen Google Font]",
        body: "[Chosen Google Font]",
        mono: "[Chosen Google Font]"
      },
      sizes: {
        xs: "0.75rem",
        sm: "0.875rem",
        base: "1rem",
        lg: "1.125rem",
        xl: "1.25rem",
        "2xl": "1.5rem",
        "3xl": "1.875rem",
        "4xl": "2.25rem",
        "5xl": "3rem"
      },
      weights: {
        light: "300",
        normal: "400",
        medium: "500",
        semibold: "600",
        bold: "700"
      }
    },
    spacing: {
      "0": "0",
      "1": "0.25rem",
      "2": "0.5rem",
      "3": "0.75rem",
      "4": "1rem",
      "6": "1.5rem",
      "8": "2rem",
      "12": "3rem",
      "16": "4rem",
      "24": "6rem"
    },
    breakpoints: {
      sm: "640px",
      md: "768px",
      lg: "1024px",
      xl: "1280px",
      "2xl": "1536px"
    },
    shadows: {
      sm: "0 1px 2px 0 rgb(0 0 0 / 0.05)",
      DEFAULT: "0 1px 3px 0 rgb(0 0 0 / 0.1)",
      md: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
      lg: "0 10px 15px -3px rgb(0 0 0 / 0.1)",
      xl: "0 20px 25px -5px rgb(0 0 0 / 0.1)"
    },
    borderRadius: {
      none: "0",
      sm: "0.125rem",
      DEFAULT: "0.25rem",
      md: "0.375rem",
      lg: "0.5rem",
      xl: "0.75rem",
      "2xl": "1rem",
      full: "9999px"
    }
  }, null, 2)
});
```

## Step 8: Validate Output

```bash
TOKENS_FILE="design-os/$PRODUCT_NAME/design-tokens.json"

# Check file exists
if [ ! -f "$TOKENS_FILE" ]; then
  echo "❌ ERROR: Design tokens file not created"
  exit 1
fi

# Check minimum file size (500 bytes)
FILE_SIZE=$(wc -c < "$TOKENS_FILE")
if [ $FILE_SIZE -lt 500 ]; then
  echo "❌ ERROR: Design tokens file too small (< 500 bytes)"
  echo "Current size: $FILE_SIZE bytes"
  exit 1
fi

# Check valid JSON
if ! jq empty "$TOKENS_FILE" 2>/dev/null; then
  echo "❌ ERROR: Design tokens file is not valid JSON"
  exit 1
fi

# Check required keys
REQUIRED_KEYS=("colors" "typography" "spacing" "breakpoints")
for key in "${REQUIRED_KEYS[@]}"; do
  if ! jq -e ".$key" "$TOKENS_FILE" >/dev/null 2>&1; then
    echo "❌ ERROR: Missing required key: $key"
    exit 1
  fi
done

# Count colors (should have at least primary, secondary, neutral = 3)
COLOR_COUNT=$(jq '.colors | keys | length' "$TOKENS_FILE")
if [ $COLOR_COUNT -lt 3 ]; then
  echo "❌ ERROR: Need at least 3 color palettes (primary, secondary, neutral)"
  exit 1
fi

echo "✓ Output validation complete ($COLOR_COUNT color palettes defined)"
```

## Completion

```
═══════════════════════════════════════════════════
        DESIGN TOKENS COMPLETE ✓
═══════════════════════════════════════════════════

Product: $ARGUMENTS
Command: /design-os/design-tokens
Version: 2.0.0

Output Created:
  ✓ design-os/$ARGUMENTS/design-tokens.json

Design System:
  Colors: [primary, secondary, neutral, semantic]
  Typography: [heading, body, mono fonts]
  Spacing: [10-scale system]
  Breakpoints: [5 responsive sizes]
  Tailwind: ✓ Compliant
  Google Fonts: ✓ Used

Validations Passed:
  ✓ Input validation (product name format)
  ✓ Prerequisites (vision.md exists)
  ✓ Valid JSON format
  ✓ All required keys present
  ✓ Minimum color palettes (≥3)
  ✓ Quality threshold (≥0.9)

NEXT STEPS:
→ /design-os/design-shell $ARGUMENTS
   Create app navigation shell and layout components

→ /design-os/shape-section $ARGUMENTS <section-name>
   Define detailed spec for a specific section

═══════════════════════════════════════════════════
```

## Guidelines

**Color Selection**:

- Use full Tailwind color scales (50-950) for flexibility
- Primary = main brand color (buttons, links, headers)
- Secondary = accent/complementary (highlights, CTAs)
- Neutral = backgrounds, text, borders (slate/gray/zinc/stone)
- Semantic = consistent success/warning/error/info states

**Typography**:

- All fonts must be available on Google Fonts
- Heading + body can be same font (modern) or different (classic)
- Mono font for code blocks, technical content
- Use consistent font weights across design

**Tailwind Compliance**:

- Use exact Tailwind color names and scales
- Use Tailwind spacing scale (0, 1, 2, 3, 4, 6, 8, 12, 16, 24)
- Use Tailwind breakpoints (sm, md, lg, xl, 2xl)
- Ensures components work seamlessly with Tailwind CSS

**Consistency**:

- These tokens will be used across ALL design-os components
- Changes here affect all screens and components
- Choose carefully - consistency is key to professional design
