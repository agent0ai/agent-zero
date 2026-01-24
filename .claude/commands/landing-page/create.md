---
description: Create and deploy a landing page using v0.dev and Vercel
argument-hint: "[--product <name>] [--type <saas|launch|leadmagnet|app|event>] [--deploy]"
model: claude-3-5-sonnet-20241022
allowed-tools:
  - Bash
  - Write
  - Read
  - AskUserQuestion
---

# Create Landing Page Command

## Overview

Creates a professional, conversion-optimized landing page using v0.dev for AI-powered design and Vercel for instant deployment.

**The `vercel-landing-page-builder` skill will activate automatically to handle this request.**

## Usage

```bash
# Interactive mode (recommended for first time)
/landing-page:create

# Quick creation with product name
/landing-page:create --product "AI Email Assistant"

# Specific type
/landing-page:create --product "TaskFlow" --type saas

# Create and deploy immediately
/landing-page:create --product "QuickLaunch" --deploy
```

## What This Command Does

1. **Gathers product information** (interactive or from arguments)
   - Product name
   - Target audience
   - Value proposition
   - Key features
   - CTA goal

2. **Generates v0.dev prompt** for AI-powered design
   - Modern, conversion-optimized structure
   - Mobile-responsive
   - Brand-consistent
   - Accessibility compliant

3. **Provides deployment instructions** for Vercel
   - Git setup
   - Vercel CLI commands
   - Custom domain configuration
   - SSL setup

4. **Configures analytics and SEO**
   - Vercel Analytics
   - PostHog (optional)
   - Meta tags
   - Open Graph
   - Structured data

5. **Delivers complete package**
   - v0.dev design link
   - Deployment commands
   - Customization guide
   - Optimization checklist

## Landing Page Types

### SaaS Product Page (`--type saas`)

**Best for:** Software products, web apps, B2B tools

**Includes:**

- Hero with clear value prop
- Problem/solution sections
- Feature highlights (3-6)
- Social proof (testimonials, logos)
- Pricing tiers
- FAQ section

**Optimization focus:** Trust, features, pricing clarity

---

### Product Launch Page (`--type launch`)

**Best for:** New product announcements, pre-launch campaigns

**Includes:**

- Countdown timer
- Launch date announcement
- Teaser content
- Early bird pricing
- Email capture form
- Social sharing

**Optimization focus:** Urgency, FOMO, exclusivity

---

### Lead Magnet Page (`--type leadmagnet`)

**Best for:** Ebook downloads, tool access, free trials

**Includes:**

- Headline (specific outcome)
- What they get (bullets)
- Visual (cover, screenshot)
- Simple form (email only)
- Privacy assurance

**Optimization focus:** Minimal friction, immediate value

---

### App Landing Page (`--type app`)

**Best for:** Mobile apps, desktop apps

**Includes:**

- App screenshots/demo video
- Feature highlights
- Platform badges (App Store, Google Play)
- Reviews and ratings
- Download CTAs

**Optimization focus:** App store optimization, visual demo

---

### Event Registration (`--type event`)

**Best for:** Webinars, conferences, workshops

**Includes:**

- Event details (date, time, location)
- Speakers and agenda
- Value proposition
- Registration form
- Countdown timer

**Optimization focus:** Speaker credibility, urgency

## Implementation

The command will ask you questions interactively, or you can provide via arguments:

### Interactive Mode

```bash
/landing-page:create
```

**Questions asked:**

1. Product name?
2. Target audience?
3. Main value proposition (one sentence)?
4. Top 3-6 features/benefits?
5. Primary CTA (sign up, demo, download, purchase)?
6. Brand colors? (optional - defaults to modern blue)
7. Existing brand assets? (optional)
8. Deploy immediately to Vercel? (yes/no)

### Argument Mode

```bash
/landing-page:create \
  --product "AI Email Assistant" \
  --audience "busy professionals" \
  --value-prop "Reduce email time from 2 hours to 20 minutes daily" \
  --features "Smart replies, Auto-triage, Learning AI" \
  --cta "Start Free Trial" \
  --type saas \
  --deploy
```

## Output

The command provides:

### 1. v0.dev Design Prompt

```
Create a modern landing page for [Product Name]

[Detailed v0 prompt with all specifications]

[Copy this to v0.dev]
```

### 2. Vercel Deployment Commands

```bash
# Initialize project
git init
git add .
git commit -m "Initial commit: [Product] landing page"

# Deploy to Vercel
vercel
vercel --prod

# Add custom domain
vercel domains add yourdomain.com
```

### 3. Configuration Files

**`vercel.json`** - Vercel configuration
**`app/layout.tsx`** - SEO metadata
**`lib/analytics.ts`** - Analytics setup

### 4. Optimization Checklist

- [ ] Review design on v0.dev
- [ ] Customize copy and imagery
- [ ] Deploy to Vercel
- [ ] Configure custom domain
- [ ] Set up analytics
- [ ] Test on mobile devices
- [ ] Run Lighthouse audit
- [ ] Launch and monitor conversions

## Post-Creation Steps

### 1. Review Design

Visit the v0.dev link provided and review the generated design.

**Iterate if needed:**

- Click "Edit" in v0.dev
- Request design changes
- Download updated code

### 2. Deploy to Vercel

Follow the Bash commands provided:

```bash
# From your project directory
vercel

# Follow prompts
# Deploy to production
vercel --prod
```

**You'll get:**

- Production URL: `https://your-project.vercel.app`
- Automatic SSL certificate
- Global CDN deployment
- Automatic preview deployments for PRs

### 3. Custom Domain

If you have a domain:

```bash
vercel domains add yourdomain.com
vercel domains add www.yourdomain.com
```

**DNS Configuration:**

```
CNAME www → cname.vercel-dns.com
A     @   → 76.76.21.21
```

### 4. Analytics Setup

**Vercel Analytics** (built-in):

- Automatically enabled
- View at: `https://vercel.com/[team]/[project]/analytics`

**PostHog** (optional, more detailed):

1. Sign up at posthog.com
2. Add API key to `.env.local`
3. Track custom events

### 5. Monitor and Optimize

**Week 1:**

- Monitor traffic and conversions
- Identify drop-off points
- Gather user feedback

**Week 2:**

- Create A/B test variants
- Test different headlines
- Optimize CTA placement

**Ongoing:**

- Iterate based on data
- Update social proof
- Refresh content quarterly

## Examples

### Example 1: SaaS Product

```bash
/landing-page:create --product "TaskFlow" --type saas
```

**Generates:**

- Hero: "Manage Tasks 3X Faster with AI-Powered Workflows"
- Features: Smart scheduling, Team collaboration, Integrations
- Pricing: Free, Pro ($29/mo), Team ($99/mo)
- Social proof: Customer logos, testimonials

### Example 2: Product Launch

```bash
/landing-page:create --product "QuickShip" --type launch
```

**Generates:**

- Countdown to launch date
- Early bird pricing ($49 → $99 after launch)
- Email capture: "Get notified 24 hours before launch"
- Social sharing: "Share and get 20% off"

### Example 3: Lead Magnet

```bash
/landing-page:create \
  --product "Ultimate Guide to AI Productivity" \
  --type leadmagnet
```

**Generates:**

- Headline: "Get the Ultimate AI Productivity Guide (Free)"
- Bullets: 47 pages, 12 tools reviewed, Implementation checklist
- Email form: Name + Email only
- Instant download

## Integration with Brand Voice

This command automatically activates the `brand-voice` skill to ensure:

- Data-driven copy (specific numbers, not vague claims)
- Value-first messaging
- Honest ROI projections
- Soft CTAs (not pushy)

## Integration with Content Optimizer

Use the `content-optimizer` skill to adapt landing page copy for social media promotion:

```bash
# After creating landing page
Create LinkedIn post promoting our new landing page at [URL]
```

## Tips for Success

### Headlines

**Do:**

- ✅ "Close Deals 3X Faster with AI Outreach"
- ✅ "Turn Visitors into Customers - Starting Today"
- ✅ "Ship Features in Days, Not Months"

**Don't:**

- ❌ "Welcome to Our Product"
- ❌ "The Best Solution"
- ❌ "Innovative Platform"

### CTAs

**Do:**

- ✅ "Start Free Trial" (benefit-focused)
- ✅ "Get Instant Access" (immediacy)
- ✅ "See Plans & Pricing" (transparency)

**Don't:**

- ❌ "Submit" (generic)
- ❌ "Click Here" (vague)
- ❌ "Learn More" (weak)

### Social Proof

**Effective:**

- Customer logos (if B2B)
- Specific testimonials with photos
- Usage stats ("Join 10,000+ teams")
- Media mentions with logos

**Less effective:**

- Generic praise without attribution
- Stock photos
- Vague numbers ("thousands of users")

## Troubleshooting

**v0.dev design not what you expected:**

- Edit the prompt and regenerate
- Request specific changes in v0.dev
- Iterate until satisfied

**Vercel deployment fails:**

```bash
# Check Vercel CLI is installed
vercel --version

# If not installed
npm i -g vercel

# Login to Vercel
vercel login
```

**Custom domain not working:**

- Check DNS propagation (can take 24-48 hours)
- Verify CNAME and A records
- Check domain registrar settings

**Analytics not tracking:**

- Verify Vercel Analytics is enabled in dashboard
- Check PostHog API key in `.env.local`
- Clear browser cache and test in incognito

## Related Commands

- `/landing-page:optimize` - Improve existing landing page conversion
- `/landing-page:ab-test` - Create A/B test variants
- `/landing-page:analyze` - Analyze landing page performance

---

*This command automates the entire landing page creation workflow from design to deployment*
