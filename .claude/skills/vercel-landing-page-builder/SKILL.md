---
name: vercel-landing-page-builder
description: Automates landing page creation using v0.dev for AI-powered design and Vercel for instant deployment. Handles product landing pages, SaaS marketing pages, launch pages, and conversion-optimized pages. Use when creating landing pages, product launches, marketing campaigns, or rapid prototyping.
---

# Vercel Landing Page Builder Skill

## What This Skill Does

Automates the complete landing page workflow:

- **AI-powered design** - Generates modern landing pages via v0.dev
- **Instant deployment** - Deploys to Vercel with custom domains
- **Conversion optimization** - Best practices for SaaS, product launches
- **Brand consistency** - Applies brand voice and visual identity
- **Analytics integration** - Sets up tracking (Vercel Analytics, Plausible, PostHog)
- **SEO optimization** - Meta tags, Open Graph, structured data
- **Performance** - Optimized for Core Web Vitals
- **A/B testing ready** - Multiple variants for testing

## When This Skill Activates

This skill automatically activates for requests like:

- "Create a landing page for [product]"
- "Build a SaaS landing page"
- "Deploy a product launch page"
- "Generate landing page from product description"
- "Create conversion-optimized page for [offer]"
- "Build and deploy landing page to Vercel"

## Landing Page Types

### 1. SaaS Product Page

**Structure:**

- Hero section (headline, subheadline, CTA)
- Problem/solution
- Key features (3-6)
- Social proof (testimonials, logos)
- Pricing tiers
- FAQ
- Final CTA

**Optimization:**

- Clear value proposition in headline
- Benefits over features
- Trust signals (security badges, testimonials)
- Multiple CTAs (above fold + bottom)

### 2. Product Launch Page

**Structure:**

- Countdown timer
- Hero with launch date
- Teaser content
- Early bird offer
- Email capture
- Social sharing

**Optimization:**

- Urgency (limited time, scarcity)
- FOMO triggers
- Exclusive early access
- Social proof (waitlist count)

### 3. Lead Magnet Page

**Structure:**

- Headline (value proposition)
- What they get (bullet points)
- Visual (ebook cover, tool screenshot)
- Form (minimal fields)
- Privacy note

**Optimization:**

- Above-fold form
- Specific outcome promised
- No navigation (focused conversion)
- Immediate delivery message

### 4. App Landing Page

**Structure:**

- App screenshots/demo
- Feature highlights
- Platform badges (App Store, Google Play)
- Reviews/ratings
- Download CTA

**Optimization:**

- Mobile-first design
- App store optimization
- Video demo
- Trust badges

### 5. Event Registration

**Structure:**

- Event details (date, time, location)
- Speakers/agenda
- Value proposition
- Registration form
- Countdown

**Optimization:**

- Calendar add buttons
- Speaker credibility
- Testimonials from past events
- Urgency (seats remaining)

## Instructions

When this skill activates, follow these steps:

### 1. Gather Product Information

**Request from user:**

- Product name
- Target audience
- Main value proposition
- Key features (3-6)
- CTA goal (sign up, demo, download, purchase)
- Brand colors (if specific)
- Existing website/brand assets (optional)

**Smart defaults:**

- If not provided, infer from product description
- Use conversion best practices
- Apply brand-voice principles

### 2. Design with v0.dev

**v0.dev prompt structure:**

```
Create a modern, conversion-optimized landing page for [product name].

Product: [description]
Target audience: [audience]
Value proposition: [main benefit]

Structure:
1. Hero Section:
   - Headline: [specific headline]
   - Subheadline: [clarifying benefit]
   - CTA: [primary action]
   - Hero image: [description]

2. Problem/Solution:
   - Problem: [pain point]
   - Solution: [how product solves it]

3. Features (3 columns):
   - [Feature 1]: [benefit]
   - [Feature 2]: [benefit]
   - [Feature 3]: [benefit]

4. Social Proof:
   - Testimonial quote
   - Customer logos (if B2B)
   - Stats (users, rating, etc.)

5. Pricing/CTA:
   - [Pricing structure or final CTA]

Design requirements:
- Modern, clean design
- Mobile-responsive
- Fast loading
- Tailwind CSS
- shadcn/ui components
- Dark mode support
- Smooth animations
- Accessibility (WCAG AA)

Brand:
- Primary color: [color or "modern blue"]
- Style: [minimalist|playful|professional|bold]

Technical:
- Next.js 14 App Router
- TypeScript
- React Server Components
```

**v0.dev usage:**

1. Submit prompt to v0.dev
2. Review generated design
3. Request iterations if needed
4. Download code when satisfied

### 3. Deploy to Vercel

**Deployment steps:**

```bash
# 1. Initialize git repo (if not already)
git init
git add .
git commit -m "Initial commit: [Product] landing page"

# 2. Create Vercel project
vercel

# Follow prompts:
# - Link to existing project? No
# - Project name: [product-name]-landing
# - Directory: ./
# - Override settings? No

# 3. Deploy to production
vercel --prod

# 4. (Optional) Add custom domain
vercel domains add [yourdomain.com]
vercel domains add www.[yourdomain.com]
```

**Vercel configuration** (`vercel.json`):

```json
{
  "git": {
    "deploymentEnabled": {
      "main": true
    }
  },
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-XSS-Protection",
          "value": "1; mode=block"
        }
      ]
    }
  ],
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/"
    }
  ]
}
```

### 4. SEO Optimization

**Add to landing page:**

```typescript
// app/layout.tsx or page metadata
export const metadata = {
  title: '[Product Name] - [Main Benefit]',
  description: '[Compelling 155-char description with CTA]',
  keywords: '[keyword1, keyword2, keyword3]',
  openGraph: {
    title: '[Product Name]',
    description: '[Social-optimized description]',
    url: 'https://[domain].com',
    siteName: '[Product Name]',
    images: [
      {
        url: 'https://[domain].com/og-image.png',
        width: 1200,
        height: 630,
        alt: '[Product screenshot/visual]',
      },
    ],
    locale: 'en_US',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: '[Product Name]',
    description: '[Twitter-optimized description]',
    images: ['https://[domain].com/og-image.png'],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
}
```

**Structured data:**

```typescript
// Add JSON-LD schema
const productSchema = {
  '@context': 'https://schema.org',
  '@type': 'Product',
  name: '[Product Name]',
  description: '[Product description]',
  brand: {
    '@type': 'Brand',
    name: '[Company Name]',
  },
  offers: {
    '@type': 'Offer',
    price: '[price]',
    priceCurrency: 'USD',
  },
}
```

### 5. Analytics Setup

**Vercel Analytics** (built-in):

```typescript
// app/layout.tsx
import { Analytics } from '@vercel/analytics/react'

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        {children}
        <Analytics />
      </body>
    </html>
  )
}
```

**PostHog** (product analytics):

```typescript
// lib/posthog.ts
import posthog from 'posthog-js'

if (typeof window !== 'undefined') {
  posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
    api_host: 'https://app.posthog.com',
  })
}

// Track CTA clicks
<button onClick={() => posthog.capture('cta_clicked', { location: 'hero' })}>
  Get Started
</button>
```

**Conversion tracking:**

```typescript
// Track key events
posthog.capture('landing_page_view')
posthog.capture('cta_clicked', { button: 'Get Started' })
posthog.capture('signup_completed')
posthog.capture('demo_requested')
```

### 6. A/B Testing (Optional)

**Create variants:**

```typescript
// app/page.tsx
import { unstable_flag as flag } from '@vercel/flags/next'

const variant = await flag('landing_page_variant')

return variant === 'A' ? (
  <HeroVariantA />
) : (
  <HeroVariantB />
)
```

**Test elements:**

- Headlines
- CTA copy
- Button colors
- Pricing display
- Social proof placement

### 7. Performance Optimization

**Checklist:**

- [ ] Image optimization (next/image)
- [ ] Font optimization (next/font)
- [ ] Code splitting (dynamic imports)
- [ ] Preload critical resources
- [ ] Minimize JavaScript
- [ ] Lazy load below fold content

**Target metrics:**

- LCP (Largest Contentful Paint): <2.5s
- FID (First Input Delay): <100ms
- CLS (Cumulative Layout Shift): <0.1

### 8. Conversion Optimization

**Above the fold:**

- [ ] Clear headline (value proposition)
- [ ] Supporting subheadline
- [ ] Primary CTA visible
- [ ] Hero image/video
- [ ] Trust signals (logos, testimonials)

**Throughout page:**

- [ ] Multiple CTAs (every 2-3 sections)
- [ ] Benefit-focused copy
- [ ] Social proof scattered
- [ ] Address objections
- [ ] Clear pricing (if applicable)

**Final CTA:**

- [ ] Recap value proposition
- [ ] Remove friction
- [ ] Create urgency
- [ ] Guarantee/risk reversal

## Output Format

```markdown
# Landing Page Created: [Product Name]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🎨 Design Generated

**v0.dev prompt used:**
```

[Copy of v0 prompt]

```

**Design URL:** https://v0.dev/[design-id]

**Components:**
- Hero section ✅
- Features section ✅
- Social proof ✅
- Pricing/CTA ✅
- [Additional sections]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🚀 Deployed to Vercel

**Production URL:** https://[project-name].vercel.app

**Custom Domain Setup:**
```bash
vercel domains add [yourdomain.com]
```

**Git Repository:** [If created]

**Deployment Status:**

- ✅ Production deployed
- ✅ SSL certificate active
- ✅ Performance optimized
- ✅ Analytics enabled

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📊 Analytics Configured

**Tracking:**

- [x] Page views
- [x] CTA clicks
- [x] Form submissions
- [x] Scroll depth

**Dashboard:** <https://vercel.com/[team]/[project]/analytics>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## ✅ SEO Optimization

- [x] Meta title and description
- [x] Open Graph tags
- [x] Twitter Card tags
- [x] Structured data (JSON-LD)
- [x] Robots.txt
- [x] Sitemap.xml

**Lighthouse Score:** [Run and display]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🎯 Conversion Optimization Checklist

**Above the Fold:**

- [x] Clear value proposition
- [x] Visible CTA
- [x] Hero image
- [x] Trust signals

**Content:**

- [x] Benefits-focused
- [x] Social proof
- [x] Address objections
- [x] Multiple CTAs

**Technical:**

- [x] Mobile-responsive
- [x] Fast loading (<3s)
- [x] Accessible (WCAG AA)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📝 Next Steps

1. **Review and Customize:**
   - Visit: https://[project-name].vercel.app
   - Review design and copy
   - Request iterations via v0.dev if needed

2. **Add Custom Domain:**

   ```bash
   vercel domains add [yourdomain.com]
   ```

3. **Configure DNS:**
   - Add CNAME record: www → cname.vercel-dns.com
   - Add A record: @ → 76.76.21.21

4. **Set Up Conversion Tracking:**
   - Configure PostHog events
   - Set up funnel analysis
   - Create dashboard

5. **Launch:**
   - Announce on social media
   - Share with target audience
   - Monitor analytics

6. **Optimize:**
   - Run A/B tests on headlines
   - Test different CTAs
   - Iterate based on data

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🔗 Resources

**Live Page:** https://[project-name].vercel.app
**Vercel Dashboard:** <https://vercel.com/[team]/[project>]
**v0.dev Design:** <https://v0.dev/[design-id>]
**Analytics:** <https://vercel.com/[team]/[project]/analytics>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

```

## Integration with Other Skills

Works seamlessly with:
- `brand-voice` - Applies consistent messaging to landing page copy
- `content-optimizer` - Optimizes copy for conversion
- `stripe-revenue-analyzer` - Uses data as social proof

## Best Practices

### Copy Writing

**Headlines:**
- Clear value proposition
- Specific benefit (not feature)
- Action-oriented
- Under 60 characters

**Example good headlines:**
- "Close Deals 3X Faster with AI-Powered Outreach"
- "Turn Visitors into Customers - Starting Today"
- "Ship Products in Days, Not Months"

**CTAs:**
- Action verbs (Get, Start, Join, Try, Download)
- Benefit-focused (not generic)
- Create urgency

**Examples:**
- ✅ "Start Free Trial" > ❌ "Sign Up"
- ✅ "Get Instant Access" > ❌ "Submit"
- ✅ "See Plans & Pricing" > ❌ "Learn More"

### Design

**Color psychology:**
- Blue: Trust, professionalism (SaaS, B2B)
- Green: Growth, money (finance, health)
- Orange: Energy, urgency (e-commerce, CTA buttons)
- Purple: Creativity, innovation (creative tools)

**CTA buttons:**
- High contrast with background
- Large enough to tap (min 44×44px)
- Whitespace around button
- Hover state clear

### Social Proof

**Placement:**
- Logo bar under hero (if B2B)
- Testimonials scattered throughout
- Stats in hero area (if impressive)
- Final social proof before bottom CTA

**Types:**
- Customer logos (B2B)
- Testimonials with photos
- Reviews/ratings
- User count
- Media mentions

---

*This skill automates the entire landing page creation and deployment workflow*
