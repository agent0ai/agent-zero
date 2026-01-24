---
description: Generate complete landing page from product definition
argument-hint: <product-name> [--template saas|app|service] [--framework tailwind|bootstrap]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Read, Write, Bash
---

Create landing page: **${ARGUMENTS}**

## Landing Page Generation

**AI Copywriting** - Hero, features, benefits, FAQ
**Responsive Design** - Mobile-first, tested layouts
**Conversion Optimized** - Based on best practices
**Zoho Integration** - Forms, tracking, analytics
**Deploy Options** - Zoho Sites, Webflow, custom hosting

## Generate Landing Page

```javascript
await Task({
  subagent_type: 'frontend-architect',
  description: 'Generate landing page',
  prompt: `Create landing page for: ${PRODUCT_NAME}

Template: ${TEMPLATE || 'saas'}
Framework: ${FRAMEWORK || 'tailwind'}

Read:
- products/${PRODUCT_NAME}-definition.md
- products/${PRODUCT_NAME}-summaries.md

Generate complete landing page with sections:

## 1. Hero Section
- Headline (from summaries)
- Sub-headline
- CTA button (primary action)
- Hero image/video placeholder
- Social proof badges

## 2. Social Proof
- Customer logos (placeholders)
- Testimonials (3-5)
- Key metrics

## 3. Features (3-5 key features)
Each feature:
- Icon
- Title
- Description (benefit-focused)
- Screenshot/visual

## 4. How It Works (3-step process)
- Step 1: [Action]
- Step 2: [Action]
- Step 3: [Result]

## 5. Benefits (Problem → Solution)
- Pain point → How we solve it
- Before/After comparison

## 6. Pricing
- Tiers from product definition
- Feature comparison table
- FAQ

## 7. Final CTA
- Sign up form (Zoho Forms)
- Lead capture fields
- Privacy notice

## 8. Footer
- Links, privacy, terms

Use ${FRAMEWORK} for styling.
Make fully responsive (mobile-first).
Include Zoho tracking code.

Generate files:
- index.html
- styles.css
- script.js

Deploy to Zoho Sites or provide hosting instructions.
  `
})
```

## Success Criteria

- ✓ Complete HTML/CSS/JS generated
- ✓ All 8 sections included
- ✓ Mobile responsive (tested)
- ✓ Zoho Forms integrated
- ✓ Conversion-optimized layout
- ✓ Fast load time (<2s)
- ✓ Deployed to Zoho Sites
- ✓ Tracking enabled

---
**Uses**: frontend-architect, design-system-architect
**Input**: Product definition + summaries
**Output**: Complete landing page (HTML/CSS/JS) + deployed URL
**Next Commands**: `/landing/optimize`, `/landing/ab-test`
