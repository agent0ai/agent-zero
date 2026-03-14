# Agent Jumbo Deployment Guide

> This guide covers deploying Agent Jumbo (Agent Jumbo DevOps fork) to Vercel with full CI/CD automation.

## Quick Start

### Prerequisites

- Node.js 18+ installed
- Vercel account (free tier OK for development)
- GitHub account with repository access
- Understanding of Next.js and environment variables

### Deploy in 5 Minutes

1. **Prepare Repository**

   ```bash
   # Clone repository
   git clone https://github.com/agent-jumbo-deploy/agent-jumbo.git
   cd agent-jumbo

   # Create feature branch for deployment setup
   git checkout -b feature/vercel-deployment
   ```

2. **Configure Local Environment**

   ```bash
   cd web
   cp .env.example .env.local

   # Edit .env.local with your values:
   # - NEXT_PUBLIC_API_URL=http://localhost:3000/api
   # - NEXT_PUBLIC_GITHUB_REPO=your-repo
   # - NEXT_PUBLIC_GA_ID=your-ga-id (optional)
   ```

3. **Test Locally**

   ```bash
   npm install
   npm run build
   npm run dev
   # Visit http://localhost:3000
   ```

4. **Deploy to Vercel**

   ```bash
   npm install -g vercel
   vercel --prod
   # Follow prompts, select your GitHub repository
   ```

5. **Configure GitHub Secrets**
   - Repository Settings → Secrets and variables → Actions
   - Add: VERCEL_TOKEN, VERCEL_ORG_ID, VERCEL_PROJECT_ID
   - Next push to main automatically deploys!

## Deployment Architecture

### Overview

Agent Jumbo uses a multi-layer deployment architecture:

```text
┌─────────────────────────────────────────────────┐
│         GitHub Repository (Main)                │
├─────────────────────────────────────────────────┤
│  Commits trigger CI/CD workflows:               │
│  1. web-build.yml (Test/Lint/Build)            │
│  2. web-deploy.yml (Vercel Deployment)         │
│  3. web-docs-check.yml (Documentation)         │
└─────────────────────────────────────────────────┘
           ↓ (on success)
┌─────────────────────────────────────────────────┐
│    Vercel Production Environment                │
├─────────────────────────────────────────────────┤
│  • Next.js 14 (React 18)                        │
│  • Serverless Functions (API routes)            │
│  • Edge Caching (static content)                │
│  • Custom Domain Support                        │
│  • Environment Variables (secure)               │
│  • Analytics Integration (Google Analytics)     │
└─────────────────────────────────────────────────┘
           ↓ (live)
┌─────────────────────────────────────────────────┐
│  Public Agent Jumbo Instance                    │
│  https://agent-jumbo.vercel.app                 │
└─────────────────────────────────────────────────┘
```

### Key Components

#### Web Application

- **Framework:** Next.js 14 with React 18
- **Styling:** Tailwind CSS with dark mode
- **Documentation:** Markdown-based with gray-matter frontmatter
- **Analytics:** Google Analytics 4 integration
- **API Routes:** /api/github, /api/deployment

#### CI/CD Pipeline

- **Build Verification:** Tests on Node 18.x and 20.x
- **Linting:** ESLint configuration (non-blocking)
- **Type Checking:** TypeScript strict mode
- **Documentation:** Markdown validation
- **Deployment:** Automated to Vercel on main branch push

#### Environment Configuration

- **Public Variables:** NEXT_PUBLIC_* (visible in browser)
- **API Configuration:** GitHub repo, deployment URLs
- **Analytics:** Google Analytics ID (optional)
- **Security:** Vercel security headers configured

## Step-by-Step Deployment

### Step 1: Repository Setup

1. Fork or clone the Agent Jumbo repository
2. Create a feature branch for deployment setup
3. Verify all files are present:

   ```bash
   # Check key deployment files
   ls -la web/.env.example      # ✓ Should exist
   ls -la web/vercel.json        # ✓ Should exist
   ls -la web/package.json       # ✓ Should exist
   ls -la .github/workflows/     # ✓ Should contain 3 workflows
   ```

### Step 2: Local Development

1. **Setup development environment:**

   ```bash
   cd web
   cp .env.example .env.local
   npm install
   npm run dev
   ```

2. **Verify application:**
   - Visit <http://localhost:3000>
   - Check home page renders
   - Test documentation loading
   - Verify dashboard displays

3. **Run build verification:**

   ```bash
   npm run build
   npm run type-check
   ```

### Step 3: Vercel Project Setup

1. **Create Vercel project:**
   - Visit [vercel.com/new](https://vercel.com/new)
   - Connect GitHub repository
   - Import "agent-jumbo" repository

2. **Configure project settings:**
   - Framework: Next.js
   - Root Directory: web/
   - Build Command: npm run build
   - Output Directory: .next
   - Install Command: npm ci

3. **Set environment variables:**
   | Variable | Example | Required |
   |----------|---------|----------|
   | NEXT_PUBLIC_API_URL | <https://api.example.com> | Yes |
   | NEXT_PUBLIC_GITHUB_REPO | agent-jumbo-deploy/agent-jumbo | Yes |
   | NEXT_PUBLIC_GA_ID | G-XXXXXXXXXX | No |
   | NEXT_PUBLIC_URL | <https://agent-jumbo.vercel.app> | Yes |

4. **Deploy:**
   - Click "Deploy" button
   - Wait for build to complete (2-5 minutes)
   - Visit deployed URL

### Step 4: GitHub Actions Integration

1. **Authenticate Vercel CLI:**

   ```bash
   vercel login
   ```

2. **Get Vercel secrets:**
   - VERCEL_TOKEN: Account Settings → Tokens → Create
   - VERCEL_ORG_ID: Project → Settings → Org ID
   - VERCEL_PROJECT_ID: Project → Settings → Project ID

3. **Add GitHub secrets:**
   - Repository Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Add three secrets (VERCEL_TOKEN, VERCEL_ORG_ID, VERCEL_PROJECT_ID)

4. **Test CI/CD:**

   ```bash
   # Make a small change
   echo "// test" >> web/lib/seo.ts
   git add .
   git commit -m "test: trigger CI/CD"
   git push

   # Watch GitHub Actions tab for workflow runs
   # Verify deployment in Vercel dashboard
   ```

### Step 5: Custom Domain (Optional)

1. **In Vercel dashboard:**
   - Project Settings → Domains
   - Add your custom domain
   - Follow DNS configuration instructions

2. **Update environment variables:**
   - Set NEXT_PUBLIC_URL to custom domain
   - Redeploy project

## Troubleshooting

### Build Failures

#### Error: "Cannot find module 'next'"

- Solution: Ensure Node 18+ installed, run `npm ci` in web/ directory
- Verify package-lock.json exists

#### Error: "TypeScript error in ..."

- Solution: Run `npm run type-check` locally to identify issues
- Fix type errors before pushing

#### Error: "Build optimization failed"

- Solution: Check Vercel build logs for specific error
- Reduce bundle size if needed

### Deployment Issues

#### Deployment never starts

- Verify VERCEL_TOKEN, VERCEL_ORG_ID, VERCEL_PROJECT_ID are set correctly
- Check GitHub Actions logs for authentication errors

#### Environment variables not working

- Verify NEXT_PUBLIC_* prefix for frontend variables
- Check Vercel project settings for variable configuration
- Redeploy after changing variables

#### Analytics not tracking

- Verify NEXT_PUBLIC_GA_ID is set in Vercel project
- Check browser console for gtag initialization
- Verify Google Analytics property ID format (G-XXXXXXXXXX)

### Documentation Not Loading

#### Markdown files not rendering

- Check that docs/ directory exists with .md files
- Verify frontmatter syntax (YAML between --- delimiters)
- Check for invalid HTML in markdown

#### CSS not applying to docs

- Verify Tailwind CSS dark mode config (darkMode: 'class')
- Check for CSS selector syntax (use .dark .prose, not dark .prose)
- Clear browser cache and rebuild

## Monitoring

### Vercel Dashboard

1. **Deployments tab:**
   - View all deployments with status
   - Rollback to previous version if needed
   - Monitor build duration

2. **Analytics tab:**
   - View page views and edge function invocations
   - Monitor error rates
   - Check performance metrics

3. **Logs tab:**
   - View build logs for debugging
   - Check runtime errors and edge function logs

### GitHub Actions

1. **Actions tab:**
   - View all workflow runs
   - Check build/deploy success rates
   - Monitor execution time

2. **Settings → Environments:**
   - View environment variables
   - Monitor secret usage

### Google Analytics

1. **Real-time reporting:**
   - View active users and page views
   - Monitor traffic sources

2. **Conversion tracking:**
   - Setup goals for important actions
   - Track API endpoint usage

## Performance Optimization

### Caching Strategy

Agent Jumbo uses Vercel's edge caching:

- Static pages: cached indefinitely
- API routes: cached based on response headers
- Documentation: cached for 1 hour

### Image Optimization

Next.js automatic image optimization:

- Images resized on-demand
- Served in modern formats (WebP when supported)
- Lazy loading enabled by default

### Code Splitting

Next.js automatic code splitting:

- Each page gets its own bundle
- Shared code extracted to common chunk
- Dynamic imports for large libraries

## Security

### Headers

Vercel security headers configured in vercel.json:

- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Referrer-Policy: strict-origin-when-cross-origin

### Environment Variables

- Never commit .env.local to repository
- Use .env.example as template
- All secrets managed via Vercel dashboard
- GitHub secrets only contain Vercel tokens

### API Security

- GitHub API calls use public endpoints (no token required)
- Deployment data is mock/simulated
- HTML content sanitized (XSS prevention)
- No sensitive data in client-side code

## Rollback Procedure

### Immediate Rollback

1. **In Vercel Dashboard:**
   - Go to Deployments tab
   - Find the previous successful deployment
   - Click the three-dot menu
   - Select "Promote to Production"

2. **Via CLI:**

   ```bash
   vercel --prod --alias=<previous-deployment-url>
   ```

### Rollback via Git

1. **Revert the problematic commit:**

   ```bash
   git revert <problematic-commit-hash>
   git push origin main
   ```

2. **Wait for deployment:**
   - GitHub Actions triggers automatically
   - Vercel builds and deploys new version
   - Monitor Vercel dashboard for completion

## Next Steps

1. **Complete local setup** (web/.env.local configuration)
2. **Verify Vercel project** (test deployment)
3. **Configure GitHub secrets** (enable CI/CD)
4. **Set up custom domain** (point to Vercel)
5. **Monitor analytics** (track user engagement)
6. **Gather feedback** (iterate on design/features)

## Support & Resources

- **Next.js Documentation:** <https://nextjs.org/docs>
- **Vercel Documentation:** <https://vercel.com/docs>
- **Tailwind CSS:** <https://tailwindcss.com/docs>
- **GitHub Actions:** <https://docs.github.com/en/actions>

---

**Document Version:** 1.0
**Last Updated:** 2026-02-01
**Status:** Production Ready
