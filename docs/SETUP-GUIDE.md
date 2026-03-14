# Agent Jumbo Team Setup Guide

> Step-by-step guide for team members to set up Agent Jumbo development and deployment environment.

## For Developers

### 1. Clone Repository

```bash
git clone https://github.com/agent-jumbo-deploy/agent-jumbo.git
cd agent-jumbo
```

### 2. Setup Web Application

```bash
cd web

# Copy environment template
cp .env.example .env.local

# Install dependencies
npm install

# Start development server
npm run dev
```

Visit <http://localhost:3000> in your browser.

### 3. Project Structure

```text
web/
├── app/                   # Next.js app directory
│   ├── layout.tsx        # Root layout with Header/Footer
│   ├── page.tsx          # Home page
│   ├── api/              # API routes
│   ├── dashboard/        # Dashboard page
│   └── documentation/    # Documentation pages
├── components/           # React components
├── lib/                  # Utilities (docs.ts, github.ts, seo.ts, etc)
├── public/               # Static assets
├── docs/                 # Markdown documentation
├── package.json          # Dependencies
├── tsconfig.json         # TypeScript config
├── tailwind.config.ts    # Tailwind CSS config
├── next.config.js        # Next.js config
└── .env.example          # Environment template
```

### 4. Common Development Tasks

**Run tests:**

```bash
npm run type-check    # TypeScript type checking
npm run lint          # ESLint linting (non-blocking)
npm run build         # Full build verification
```

**Add a new page:**

1. Create file: `app/new-page/page.tsx`
2. Add component and export as default
3. Automatically routed to /new-page

**Add documentation:**

1. Create file: `docs/my-article.md`
2. Add YAML frontmatter at top
3. Automatically available at /documentation/my-article

**Update styling:**

- Tailwind CSS classes in components
- Dark mode: `dark:bg-slate-900` for dark variants
- Global styles: `app/globals.css`

### 5. Git Workflow

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes and commit
git add .
git commit -m "feat: add my feature"

# Push and create PR
git push origin feature/my-feature

# GitHub Actions automatically tests your PR
# When approved and merged, Vercel auto-deploys
```

### 6. Debugging

**Check logs locally:**

```bash
# Development server logs
npm run dev

# Build logs
npm run build 2>&1 | grep -i error

# Type checking
npm run type-check
```

**Check Vercel logs:**

1. Visit [vercel.com](https://vercel.com)
2. Select "agent-jumbo" project
3. Go to "Deployments" tab
4. Click deployment and view "Build logs"

## For DevOps/Deployment

### 1. Initial Vercel Setup

```bash
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Link project
vercel link

# Pull production environment
vercel env pull
```

### 2. Environment Variables Setup

**Local Development:**

1. Copy `.env.example` to `.env.local`
2. Fill in your local values
3. Never commit `.env.local`

**Vercel Production:**

1. Go to Vercel Dashboard → agent-jumbo → Settings
2. Go to "Environment Variables"
3. Add required variables:
   - NEXT_PUBLIC_API_URL
   - NEXT_PUBLIC_GITHUB_REPO
   - NEXT_PUBLIC_URL
   - NEXT_PUBLIC_GA_ID (optional)

**GitHub Actions:**

1. Go to Repository Settings → Secrets and variables
2. Add three repository secrets:
   - VERCEL_TOKEN (from Vercel account settings)
   - VERCEL_ORG_ID (from Vercel project settings)
   - VERCEL_PROJECT_ID (from Vercel project settings)

### 3. Monitoring Deployments

**Vercel Dashboard:**

- View all deployments
- Monitor performance metrics
- Check error rates
- View analytics

**GitHub Actions:**

- Monitor CI/CD workflow runs
- Check build/test results
- View deployment logs

**Google Analytics:**

- Monitor user traffic
- Track page views
- Monitor conversion goals

### 4. Troubleshooting Deployments

**If build fails:**

1. Check Vercel build logs for error message
2. Reproduce locally: `npm run build`
3. Fix issue and push to trigger rebuild

**If deployment hangs:**

1. Check GitHub Actions status
2. Verify Vercel secrets are set correctly
3. Check Vercel project status page

**If site is slow:**

1. Check Vercel Analytics for bottlenecks
2. Monitor API response times
3. Check for large unoptimized assets

### 5. Scaling Considerations

**As traffic increases:**

- Vercel automatically scales serverless functions
- Edge caching handles static content
- Monitor costs in Vercel dashboard

**Custom domain setup:**

1. In Vercel Settings → Domains
2. Add your custom domain
3. Follow DNS configuration
4. Update NEXT_PUBLIC_URL environment variable

## Troubleshooting Checklist

- [ ] Node.js 18+ installed (`node --version`)
- [ ] npm dependencies installed (`npm ci`)
- [ ] Environment variables configured (`.env.local` present)
- [ ] Development server running (`npm run dev`)
- [ ] No TypeScript errors (`npm run type-check`)
- [ ] Build succeeds locally (`npm run build`)
- [ ] Vercel project created and linked
- [ ] GitHub secrets configured for CI/CD
- [ ] Can access deployed site via Vercel URL
- [ ] Custom domain configured (if using one)

## Getting Help

- **Local development issues:** Check Next.js and Tailwind CSS docs
- **Vercel deployment issues:** Check Vercel deployment logs and docs
- **GitHub Actions issues:** Check workflow logs in Actions tab
- **Performance issues:** Monitor via Vercel Analytics and Google Analytics

## Quick Reference

| Task | Command |
|------|---------|
| Start dev server | `npm run dev` |
| Build for production | `npm run build` |
| Check types | `npm run type-check` |
| Run linting | `npm run lint` |
| Deploy to Vercel | `vercel --prod` |
| View Vercel logs | `vercel logs` |

---

**Document Version:** 1.0
**Last Updated:** 2026-02-01
