# Agent Jumbo - Vercel Deployment Guide

This guide provides comprehensive instructions for deploying Agent Jumbo to Vercel.

## Prerequisites

- Node.js 18+ installed locally
- Vercel account ([vercel.com](https://vercel.com))
- Vercel CLI installed (`npm i -g vercel`)
- GitHub account connected to Vercel (for GitHub integration)
- Git installed and configured

## Local Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/agent-jumbo-deploy/agent-jumbo.git
cd agent-jumbo/web
```

### 2. Copy and Configure Environment Variables

```bash
cp .env.example .env.local
# Edit .env.local and add your configuration values
# Do NOT commit .env.local to version control
```

Environment variables needed for local development:

- `NEXT_PUBLIC_API_URL`: Your API endpoint (e.g., `http://localhost:8000`)
- `NEXT_PUBLIC_GITHUB_REPO`: Repository identifier (e.g., `agent-jumbo-deploy/agent-jumbo`)
- `NEXT_PUBLIC_GA_ID`: Google Analytics ID (optional, leave empty to skip)
- `NEXT_PUBLIC_URL`: Application URL (e.g., `http://localhost:3000`)

### 3. Install Dependencies

```bash
npm install
```

### 4. Run Development Server

```bash
npm run dev
```

Visit `http://localhost:3000` to verify the application is running.

## Vercel Deployment

### Option 1: Deploy via Vercel Dashboard (Recommended)

This is the easiest and most common way to deploy.

#### Step 1: Import Project

1. Go to [vercel.com/dashboard](https://vercel.com/dashboard)
2. Click "Add New Project" or "New Project"
3. Click "Import Git Repository"
4. Search for and select the Agent Jumbo repository

#### Step 2: Configure Project Settings

In the "Configure Project" screen:

1. **Select Framework**: Next.js (auto-detected)
2. **Root Directory**: Select `web/` from the dropdown
3. **Build Command**: Should be `npm run build` (auto-detected)
4. **Output Directory**: Should be `.next` (auto-detected)
5. **Install Command**: Should be `npm install` (auto-detected)

#### Step 3: Add Environment Variables

Click "Environment Variables" and add:

| Variable | Value | Required |
|----------|-------|----------|
| `NEXT_PUBLIC_API_URL` | Your API endpoint (e.g., `https://api.example.com`) | Yes |
| `NEXT_PUBLIC_GITHUB_REPO` | `agent-jumbo-deploy/agent-jumbo` | Yes |
| `NEXT_PUBLIC_URL` | Your production domain (e.g., `https://agent-jumbo.vercel.app`) | Yes |
| `NEXT_PUBLIC_GA_ID` | Your Google Analytics ID (e.g., `G-XXXXXXXXXX`) | No |
| `NEXT_PUBLIC_ENABLE_BETA_FEATURES` | `false` | No |

#### Step 4: Deploy

Click "Deploy" and wait for the build to complete (typically 2-5 minutes).

Once deployed, you'll see your project URL in the format: `https://your-project-name.vercel.app`

### Option 2: Deploy via Vercel CLI

For automated deployments or CI/CD integration:

#### Step 1: Authenticate

```bash
vercel login
# Follow the authentication prompts
```

#### Step 2: Deploy

From the `web/` directory:

```bash
# Deploy to preview environment
vercel

# Deploy to production
vercel --prod
```

The CLI will guide you through project setup if it's your first deployment.

#### Step 3: Configure Environment Variables

If using CLI for the first time, add environment variables interactively:

```bash
vercel env add NEXT_PUBLIC_API_URL
vercel env add NEXT_PUBLIC_GITHUB_REPO
vercel env add NEXT_PUBLIC_URL
# ... repeat for other variables
```

Or edit variables in the Vercel Dashboard (Project Settings > Environment Variables).

## Environment Variables Reference

### Required Variables

#### NEXT_PUBLIC_API_URL

- The base URL for your API endpoints
- Example: `https://api.example.com`
- Used for GitHub stats and data fetching

#### NEXT_PUBLIC_GITHUB_REPO

- GitHub repository identifier
- Format: `owner/repo`
- Example: `agent-jumbo-deploy/agent-jumbo`
- Used for repository statistics and information

#### NEXT_PUBLIC_URL

- The public URL where your application is deployed
- Example: `https://agent-jumbo.vercel.app`
- Used for canonical URLs and redirects

### Optional Variables

#### NEXT_PUBLIC_GA_ID

- Google Analytics 4 Measurement ID
- Format: `G-XXXXXXXXXX`
- Leave empty to disable analytics
- Obtain from: [Google Analytics Dashboard](https://analytics.google.com)

#### NEXT_PUBLIC_ENABLE_BETA_FEATURES

- Feature flag for beta functionality
- Values: `true` or `false`
- Default: `false`

## Post-Deployment Verification

After deployment, verify the following:

### 1. Site Access

- [ ] Website loads without errors
- [ ] No 404 or 500 errors in console
- [ ] CSS and styling applied correctly

### 2. Documentation

- [ ] Documentation pages render correctly
- [ ] Code snippets display properly
- [ ] Images and assets load

### 3. Features

- [ ] Dashboard displays properly
- [ ] GitHub stats load (if API configured)
- [ ] Navigation works correctly

### 4. Analytics

- [ ] Analytics tracking active (if GA ID configured)
- [ ] No consent/privacy issues
- [ ] Analytics events fire correctly

### 5. Performance

- [ ] Page loads quickly
- [ ] No unoptimized images warnings
- [ ] Lighthouse score acceptable

## Monitoring & Maintenance

### View Deployments

In Vercel Dashboard:

1. Navigate to your project
2. Click "Deployments" tab
3. View all deployment history
4. Check build logs for errors

### View Analytics

In Vercel Dashboard:

1. Navigate to your project
2. Click "Analytics" tab
3. Monitor performance metrics
4. Check edge function usage

### Automatic Deployments

By default, Vercel automatically deploys when you push to your main branch:

```bash
git push origin main  # Automatically triggers deployment
```

To disable automatic deployments:

1. Go to Project Settings
2. Click "Git"
3. Toggle "Auto-deploy on push"

## Troubleshooting

### Build Fails with "Cannot find module"

**Cause**: Missing dependencies or incorrect Node.js version

**Solution**:

1. Verify Node.js version: `node --version` (should be 18+)
2. Check `package.json` has all required dependencies
3. Rebuild: Clear build cache and redeploy
4. In Vercel Dashboard: Settings > Git > Rebuild on push

### Environment Variables Not Working

**Cause**: Variables not set in Vercel or using wrong name format

**Solution**:

1. Verify variable names in Vercel Dashboard (Settings > Environment Variables)
2. Ensure names match exactly (case-sensitive)
3. For `NEXT_PUBLIC_*` variables, rebuild required
4. Check `.env.example` for correct variable names

### Analytics Not Tracking

**Cause**: Google Analytics ID not set or not configured correctly

**Solution**:

1. Verify `NEXT_PUBLIC_GA_ID` is set in Vercel
2. Confirm GA ID format is correct (starts with `G-`)
3. Check Google Analytics dashboard for data
4. Verify GA property matches your domain

### GitHub Stats Not Loading

**Cause**: API not configured or GitHub token missing

**Solution**:

1. Verify `NEXT_PUBLIC_GITHUB_REPO` is correct format (`owner/repo`)
2. Check `NEXT_PUBLIC_API_URL` is accessible
3. If using private repo, provide valid GitHub token
4. Check browser console for specific errors

### Slow Build Times

**Cause**: Large dependencies or unoptimized build

**Solution**:

1. Check for unused dependencies: `npm audit`
2. Review build logs for bottlenecks
3. Consider using Turbo for monorepo optimization
4. Optimize images and assets

### Deployment URL Inconsistent

**Cause**: Different URLs in development vs. production

**Solution**:

1. Update `NEXT_PUBLIC_URL` to match deployment domain
2. Verify API endpoint URLs are correct for environment
3. Check for hardcoded localhost URLs in code

## Rollback

To revert to a previous deployment:

### Via Dashboard

1. Go to Vercel Dashboard
2. Select your project
3. Click "Deployments" tab
4. Find the previous stable deployment
5. Click the three dots (...) menu
6. Select "Promote to Production"

### Via CLI

```bash
# List deployments
vercel list

# Promote specific deployment
vercel promote <deployment-url>
```

## Automatic Rollback

Vercel automatically detects build failures and maintains the previous working deployment. Failed deployments won't go to production.

## Custom Domain Setup

To use a custom domain instead of `vercel.app`:

### Add Custom Domain

1. Go to Project Settings
2. Click "Domains"
3. Click "Add Domain"
4. Enter your custom domain
5. Follow DNS configuration instructions

### DNS Configuration

For custom domains, add these DNS records:

- CNAME: `<your-project>.vercel.app`
- Or use Vercel's nameservers for simpler setup

## SSL/TLS Certificate

Vercel automatically provides free SSL/TLS certificates for all domains.

## Performance Optimization

### Image Optimization

Vercel includes Next.js Image Optimization:

- Automatic format conversion (WebP for modern browsers)
- Responsive image sizing
- Lazy loading

### Code Splitting

Next.js automatically code-splits pages:

- Faster initial page load
- Automatic lazy-loading of components

### Caching Strategy

Configure in `vercel.json`:

- Static assets cached at edge
- ISR (Incremental Static Regeneration) supported
- API routes cached per configuration

## Security Headers

Vercel.json includes security headers:

- `X-Content-Type-Options: nosniff` - Prevent MIME sniffing
- `X-Frame-Options: SAMEORIGIN` - Prevent clickjacking
- `X-XSS-Protection: 1; mode=block` - Enable XSS filtering

## Next Steps

After successful deployment:

1. **Set up monitoring**: Enable Vercel Analytics
2. **Configure CI/CD**: Connect GitHub for automatic deployments
3. **Add custom domain**: Set up your own domain name
4. **Monitor performance**: Use Vercel Analytics and Google Analytics
5. **Set up backups**: Consider database backup strategy
6. **Team collaboration**: Add team members to Vercel project

## Support & Documentation

- [Vercel Documentation](https://vercel.com/docs)
- [Next.js Documentation](https://nextjs.org/docs)
- [Vercel Community](https://vercel.com/community)
- [GitHub Issues](https://github.com/agent-jumbo-deploy/agent-jumbo/issues)

## Related Documentation

- [Local Development Setup](./README.md)
- [Environment Configuration](./.env.example)
- [Build Configuration](./next.config.js)
- [Vercel Configuration](./vercel.json)
