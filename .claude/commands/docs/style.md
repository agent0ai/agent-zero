---
description: Apply consistent styling and branding to documents
argument-hint: [--brand-guide <path>] [--colors <palette>] [--fonts <family>] [--apply-to <files>]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Read, Glob, Grep, Write, Bash
---

# Document Styling and Branding Command

Apply consistent corporate styling, branding, and visual identity to documents automatically.

## ROI: $25,000/year

- 95% reduction in branding inconsistencies
- Save 20 hours/month on manual styling corrections
- Eliminate $8K/year in design review costs
- Instant brand compliance across all documents
- Automated style guide enforcement

## Key Benefits

- **Brand Consistency**: Automatically apply corporate style guides
- **Color Management**: Enforce brand color palettes across documents
- **Typography Control**: Consistent font usage and hierarchy
- **Logo Placement**: Automatic logo positioning and sizing
- **Compliance**: Ensure regulatory and brand guideline compliance

## Implementation Steps

### Step 1: Brand Guide Analysis and Import

Collect brand assets and guidelines:

- Corporate logos (primary, secondary, monochrome variants)
- Color palettes (primary, secondary, accent, neutral colors)
- Typography specifications (heading fonts, body fonts, sizes)
- Layout guidelines (margins, spacing, grid systems)
- Imagery standards (photography style, illustration guidelines)
- Legal requirements (copyright, disclaimers, disclosures)

Parse brand guide documents:

- Extract hex color codes from brand guidelines
- Identify font families and weights
- Document spacing and margin specifications
- Catalog logo usage rules
- Note restricted elements and usage guidelines

Create brand configuration file:

```json
{
  "brand_name": "Acme Corporation",
  "version": "2.0",
  "colors": {
    "primary": "#003366",
    "secondary": "#66CCFF",
    "accent": "#FF6B35",
    "neutral_dark": "#333333",
    "neutral_light": "#F5F5F5",
    "success": "#28A745",
    "warning": "#FFC107",
    "error": "#DC3545"
  },
  "typography": {
    "heading_font": "Montserrat",
    "body_font": "Open Sans",
    "code_font": "Consolas",
    "sizes": {
      "h1": "32pt",
      "h2": "24pt",
      "h3": "18pt",
      "body": "12pt",
      "caption": "10pt"
    }
  },
  "logos": {
    "primary": "./assets/logo-primary.svg",
    "secondary": "./assets/logo-secondary.svg",
    "monochrome": "./assets/logo-mono.svg"
  },
  "spacing": {
    "margins": "1.0in",
    "line_height": "1.5",
    "paragraph_spacing": "12pt"
  }
}
```

### Step 2: Color Palette Application

Apply brand colors systematically:

- **Headings**: Use primary brand color or black
- **Links**: Use primary or accent color with hover states
- **Callouts**: Use secondary color for backgrounds
- **Success/Warning/Error**: Use designated status colors
- **Charts and Graphs**: Use brand color palette

Ensure color accessibility:

- Verify contrast ratios meet WCAG 2.1 AA standards (4.5:1 for body text, 3:1 for large text)
- Test color combinations for colorblind accessibility
- Provide alternative indicators beyond color (icons, patterns)
- Use sufficient lightness/darkness differentiation

Replace non-brand colors:

- Scan document for color usage
- Map existing colors to nearest brand colors
- Replace or flag non-compliant colors
- Document color usage for review

Create color usage guidelines:

```
Primary (#003366):
  - Use for: Main headings, primary CTA buttons, brand elements
  - Avoid: Body text, large background areas

Secondary (#66CCFF):
  - Use for: Subheadings, callouts, accents, info boxes
  - Avoid: Primary headings, critical warnings

Accent (#FF6B35):
  - Use for: Highlights, important callouts, action items
  - Avoid: Large text blocks, backgrounds
```

### Step 3: Typography and Font Management

Apply brand typography:

- **Headings**: Use brand heading font (Montserrat, Arial, etc.)
- **Body Text**: Use brand body font (Open Sans, Helvetica, etc.)
- **Code Blocks**: Use monospace font (Consolas, Monaco, Courier New)
- **Captions**: Use body font at smaller size with reduced opacity

Configure font hierarchy:

- **H1**: Brand heading font, 32pt, Bold, Primary color
- **H2**: Brand heading font, 24pt, Bold, Primary/Black
- **H3**: Brand heading font, 18pt, Semi-Bold, Black
- **H4**: Brand heading font, 14pt, Bold, Black
- **Body**: Brand body font, 12pt, Regular, Dark gray
- **Caption**: Brand body font, 10pt, Regular, Medium gray
- **Code**: Monospace, 11pt, Regular, Dark background

Handle font embedding and fallbacks:

- Embed brand fonts in PDFs for consistency
- Define web-safe fallbacks for HTML: "Montserrat, Arial, sans-serif"
- Provide font files for DOCX templates
- Test font rendering across platforms
- License fonts appropriately for distribution

Optimize typography for readability:

- Line height: 1.5x font size for body text
- Line length: 50-75 characters optimal
- Paragraph spacing: 12pt between paragraphs
- Letter spacing: Default (adjust only for headings if needed)
- Text alignment: Left-aligned for body, centered for headings (optional)

### Step 4: Logo Placement and Sizing

Configure logo usage:

- **Header**: Company logo top-left or centered, height 0.5-0.75 inches
- **Footer**: Optional smaller logo or wordmark
- **Cover Page**: Larger logo, prominently placed, height 1-2 inches
- **Watermark**: Faint logo in background (optional, for drafts)

Apply logo usage rules:

- Maintain minimum clear space around logo (equal to logo height)
- Never stretch or distort logo
- Use appropriate logo variant (color vs. monochrome)
- Ensure logo is high resolution (300 DPI for print)
- Use SVG format when possible for scalability

Create logo placement guidelines:

```
Header Logo:
  - Position: Top-left corner
  - Size: 0.75 inches height
  - Margin: 0.5 inches from top and left edges
  - Clear space: 0.75 inches on all sides

Cover Page Logo:
  - Position: Centered or top-center
  - Size: 1.5-2 inches height
  - Margin: 1 inch from top
  - Clear space: 2 inches on all sides
```

### Step 5: Layout and Spacing Standardization

Apply consistent margins:

- **Standard documents**: 1.0 inch on all sides
- **Bound documents**: 1.25 inches on binding side
- **Narrow margins**: 0.75 inches (use sparingly)
- **Wide margins**: 1.5 inches (executive documents)

Set paragraph and line spacing:

- **Line height**: 1.5x for body text, 1.2x for headings
- **Paragraph spacing**: 12pt after paragraphs (no indent), or 0.5 inch first-line indent (no spacing)
- **Section breaks**: 24-48pt before major sections
- **List spacing**: 6pt between list items

Configure page layout:

- **Page size**: Letter (8.5" x 11") or A4 (210mm x 297mm)
- **Orientation**: Portrait (default) or Landscape (tables/charts)
- **Columns**: Single column (default) or Multi-column (newsletters)
- **Gutters**: 0.5 inches for multi-column layouts

### Step 6: Headers, Footers, and Page Elements

Design branded headers:

```
Header Layout:
  ┌────────────────────────────────────────────┐
  │  [Logo]          Title          Page 5 of 23│
  └────────────────────────────────────────────┘
```

Design branded footers:

```
Footer Layout:
  ┌────────────────────────────────────────────┐
  │  Confidential  |  © 2025 Acme Corp  |  Contact│
  └────────────────────────────────────────────┘
```

Configure page numbering:

- **Position**: Bottom-right or bottom-center
- **Format**: "Page X of Y" or just "X"
- **Starting page**: Usually page 2 (skip title page)
- **Different first page**: Yes (no header/footer on title page)
- **Different odd/even**: Optional (for bound documents)

Add branded watermarks:

- **Drafts**: "DRAFT" watermark diagonal across page
- **Confidential**: "CONFIDENTIAL" watermark
- **Internal Only**: "INTERNAL USE ONLY" watermark
- Opacity: 10-20% (subtle, not distracting)
- Font: Large, all-caps, rotated 45 degrees

### Step 7: Component Styling

Style tables with brand colors:

- **Header row**: Primary brand color background, white text, bold
- **Alternating rows**: Neutral light color (#F5F5F5) and white
- **Borders**: Neutral dark color (#CCCCCC), 1pt solid
- **Cell padding**: 8-12pt for comfortable spacing
- **Caption**: Below table, brand body font, 10pt, center-aligned

Style figures and images:

- **Borders**: Optional thin border in neutral color
- **Shadows**: Subtle drop shadow (optional)
- **Captions**: Below image, brand body font, 10pt, italic
- **Alignment**: Center (default) or left/right with text wrap
- **Spacing**: 12-24pt above and below images

Style callout boxes:

```
Info Callout:
  - Background: Secondary color at 20% opacity
  - Border: 3pt left border in secondary color
  - Padding: 16pt all sides
  - Icon: Info icon in secondary color

Warning Callout:
  - Background: Warning color at 20% opacity
  - Border: 3pt left border in warning color
  - Padding: 16pt all sides
  - Icon: Warning icon in warning color
```

Style code blocks:

- **Background**: Dark gray (#1E1E1E) or neutral light (#F5F5F5)
- **Text color**: White or black (contrast with background)
- **Font**: Monospace (Consolas, Monaco, Courier New)
- **Syntax highlighting**: Use brand colors for keywords
- **Line numbers**: Optional, gray color
- **Padding**: 12-16pt all sides
- **Border radius**: 4px for rounded corners (optional)

### Step 8: Brand Compliance Validation

Check color compliance:

- Verify all colors match approved brand palette
- Flag any non-brand colors for review
- Ensure color contrast meets accessibility standards
- Test colorblind accessibility with simulation tools

Check typography compliance:

- Verify correct font families used throughout
- Check font sizes match brand specifications
- Ensure font weights are appropriate
- Validate line heights and spacing

Check logo usage compliance:

- Logo not stretched or distorted
- Sufficient clear space maintained
- Appropriate logo variant used
- High resolution (not pixelated)
- Correct placement and sizing

Check layout compliance:

- Margins meet brand specifications
- Spacing is consistent throughout
- Page elements align to grid
- Headers and footers formatted correctly

### Step 9: Multi-Document Batch Styling

Apply styles to multiple documents:

- Select documents or document folder
- Choose brand guide to apply
- Configure styling options
- Process documents in batch
- Generate styling report

Batch processing workflow:

1. Scan directory for documents (PDF, DOCX, MD, HTML)
2. Analyze current styling of each document
3. Generate style transformation plan
4. Apply brand styles systematically
5. Validate results for each document
6. Report any issues or warnings
7. Save styled documents to output directory

Handle edge cases:

- Documents with custom styling (preserve or override?)
- Mixed document types (different processes for each format)
- Locked or protected documents (require unlocking)
- Documents with embedded fonts (replace or preserve?)

### Step 10: Style Guide Export and Documentation

Create comprehensive style guide document:

- **Overview**: Brand identity and usage philosophy
- **Color Palette**: All colors with hex codes and usage guidelines
- **Typography**: Font families, sizes, hierarchy, examples
- **Logo Usage**: Placement rules, sizing, clear space, variants
- **Layout Standards**: Margins, spacing, grid systems
- **Component Styles**: Tables, images, callouts, code blocks
- **Templates**: Pre-styled templates for common document types
- **Dos and Don'ts**: Visual examples of correct and incorrect usage

Export brand package:

```
brand-guide-package/
  ├── brand-guide.pdf (comprehensive guide)
  ├── brand-config.json (machine-readable config)
  ├── colors/ (color swatches and palettes)
  ├── fonts/ (licensed font files)
  ├── logos/ (all logo variants)
  ├── templates/ (pre-styled document templates)
  └── examples/ (sample branded documents)
```

Distribute to stakeholders:

- Marketing and communications teams
- Document creators across organization
- External agencies and contractors
- Brand compliance team
- IT and template administrators

## Usage Examples

### Example 1: Apply Brand Styles to Single Document

```bash
/style --brand-guide ./acme-brand.json --apply-to ./draft-report.docx --output ./branded-report.docx
```

**Input**: Draft document + brand guide
**Output**: Fully branded document with:

- Corporate color palette applied
- Brand fonts throughout
- Logo in header and cover page
- Consistent spacing and margins
- Branded headers and footers

### Example 2: Batch Style Multiple Documents

```bash
/style --brand-guide ./acme-brand.json --apply-to ./documents/*.docx --output ./branded/
```

**Input**: Directory of 15 draft documents
**Output**: All documents styled consistently with:

- Same color palette
- Same typography
- Same logo placement
- Same headers/footers
- Batch processing report showing results

### Example 3: Create Custom Color Palette

```bash
/style --create-palette --primary "#003366" --secondary "#66CCFF" --accent "#FF6B35" --output ./custom-palette.json
```

**Output**: Color palette file with:

- Primary, secondary, and accent colors
- Auto-generated complementary colors
- Accessibility-tested combinations
- Usage guidelines for each color

### Example 4: Validate Brand Compliance

```bash
/style --validate ./annual-report.pdf --against ./acme-brand.json --report ./compliance-report.html
```

**Output**: Detailed compliance report showing:

- Colors used vs. brand palette
- Fonts found vs. brand fonts
- Logo usage compliance
- Layout and spacing issues
- Overall compliance score (87%)

### Example 5: Extract Styles from Existing Document

```bash
/style --extract-from ./well-designed-doc.pdf --output ./extracted-styles.json
```

**Output**: Style configuration extracted from document:

- Color palette detected
- Font families and sizes identified
- Spacing and margin measurements
- Can be used as basis for new brand guide

## Quality Control Checklist

- [ ] All colors match approved brand palette
- [ ] Brand fonts used consistently throughout
- [ ] Logo placement follows brand guidelines
- [ ] Logo maintains minimum clear space
- [ ] Logo is high resolution (not pixelated)
- [ ] Color contrast meets WCAG 2.1 AA standards
- [ ] Typography hierarchy is consistent
- [ ] Line heights and spacing match brand specs
- [ ] Margins and layout follow guidelines
- [ ] Headers and footers are properly styled
- [ ] Page numbers are correctly formatted
- [ ] Tables use branded colors and styling
- [ ] Callout boxes match brand style
- [ ] Code blocks are consistently styled
- [ ] No unauthorized colors or fonts
- [ ] Watermarks applied correctly (if needed)
- [ ] Document passes brand compliance validation
- [ ] Styling is consistent across all pages
- [ ] Multi-format exports maintain styling
- [ ] All stakeholders approve final styling

## Best Practices

### Color Usage Excellence

- Use primary color sparingly for maximum impact
- Leverage neutral colors for majority of content
- Ensure sufficient contrast for readability
- Test colors in both print and digital formats
- Consider colorblind accessibility in color choices
- Use brand colors consistently across all materials

### Typography Best Practices

- Limit font families to 2-3 maximum
- Maintain clear visual hierarchy with font sizes
- Use font weights purposefully (bold for emphasis)
- Ensure fonts are licensed for intended use
- Test fonts across different platforms and devices
- Provide fallback fonts for web and cross-platform compatibility

### Logo Usage Guidelines

- Always use original logo files (never recreate)
- Maintain aspect ratio (never stretch or squish)
- Use appropriate logo variant for background color
- Ensure logo is legible at all sizes
- Protect logo with adequate clear space
- Position logo consistently across documents

### Layout Consistency

- Use templates for common document types
- Align elements to invisible grid for professional appearance
- Maintain consistent margins across all pages
- Use white space generously—don't overcrowd
- Break long documents into logical sections
- Ensure page breaks occur at natural points

### Accessibility Considerations

- Meet WCAG 2.1 AA standards minimum (4.5:1 contrast for body text)
- Don't rely on color alone to convey information
- Use descriptive alt text for images and logos
- Ensure sufficient font sizes (minimum 12pt for body text)
- Test with screen readers and accessibility tools
- Provide text alternatives for visual elements

### Common Pitfalls to Avoid

- **Don't** use off-brand colors even if "close enough"
- **Don't** stretch or distort logos to fit spaces
- **Don't** mix multiple font families unnecessarily
- **Don't** ignore accessibility requirements
- **Don't** apply styling inconsistently across documents
- **Don't** override brand guidelines without approval
- **Don't** forget to test styling in all output formats

### Pro Tips for Advanced Users

- Create style presets for common use cases
- Build automated brand compliance checking into workflows
- Maintain version control for brand guidelines
- Set up style validation in CI/CD pipelines
- Create visual brand style gallery for easy reference
- Implement automated style synchronization across platforms
- Use variables/tokens for easy brand updates

## Integration Points

### Related Commands

- `/format` - Format documents with brand styles
- `/template` - Create branded templates
- `/convert` - Convert documents while preserving styles

### Tool Integrations

- **Adobe Creative Suite**: Import brand assets from Illustrator/Photoshop
- **Sketch/Figma**: Export design tokens to brand config
- **Microsoft Word**: Apply styles via DOCX templates
- **CSS/SCSS**: Generate web stylesheets from brand config
- **Pantone**: Convert print colors to digital equivalents

### Workflow Connections

1. **Design Brand** → `/style --create-palette` → **Brand Config**
2. **Brand Config** → `/style --apply-to` → **Branded Documents**
3. **Document** → `/style --validate` → **Compliance Report**
4. **Existing Doc** → `/style --extract-from` → **Reusable Style Config**
5. **Batch Documents** → `/style --apply-to batch` → **Consistent Brand**

## Success Criteria

### Brand Consistency

- 100% color palette compliance across all documents
- Consistent typography throughout all materials
- Proper logo usage in all applications
- Uniform spacing and layout standards
- Zero unauthorized branding deviations

### Quality Standards

- All colors meet accessibility contrast requirements (WCAG 2.1 AA)
- Typography is readable and professional
- Logos are high resolution and properly placed
- Layout is consistent and aesthetically pleasing
- Documents render correctly in all target formats

### Efficiency Gains

- 95% reduction in manual styling time
- 80% fewer branding inconsistency corrections
- Automated brand compliance validation
- Batch styling of 100+ documents in minutes
- Instant brand updates across all materials

### User Adoption

- 90%+ of documents use approved brand styles
- Zero manual styling by end users (automated)
- High satisfaction with branded output
- Easy brand guide adherence for all users
- Reduced need for design expertise

### Measurable Outcomes

- Time savings: 20 hours/month on styling corrections
- Cost reduction: $8K/year in design review fees
- Quality improvement: 98% brand compliance rate
- Consistency: Zero brand violations in final documents
- Scalability: Support for 1000+ documents with consistent branding
