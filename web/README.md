# Agent Jumbo

> Agent Jumbo is Agent Jumbo DevOps fork - a modern DevOps deployment and orchestration platform with an intuitive web interface, comprehensive documentation, and production-ready CI/CD automation.

## Quick Start

### Development

```bash
cd web
cp .env.example .env.local
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### Deployment

Deploy to Vercel in minutes:

```bash
npm install -g vercel
vercel --prod
```

See [../docs/DEPLOYMENT.md](../docs/DEPLOYMENT.md) for detailed instructions.

## Documentation

- **[Deployment Guide](../docs/DEPLOYMENT.md)** - Complete deployment instructions
- **[Setup Guide](../docs/SETUP-GUIDE.md)** - Team setup and development guide
- **[Vercel Setup](README-VERCEL.md)** - Vercel-specific configuration
- **[Web Documentation](app/documentation)** - In-app documentation

## Features

- ✨ **Modern Web UI** - Next.js 14 with React 18
- 🎨 **Beautiful Design** - Tailwind CSS with dark mode support
- 📊 **Analytics** - Google Analytics 4 integration
- 🚀 **Fast Deployment** - Vercel serverless deployment
- 🤖 **CI/CD Automation** - GitHub Actions workflows
- 📚 **Documentation** - Markdown-based documentation system
- 🔒 **Security** - XSS prevention, security headers configured
- 📱 **Responsive** - Mobile-first responsive design

## Tech Stack

- **Frontend:** Next.js 14, React 18, TypeScript, Tailwind CSS
- **Deployment:** Vercel (serverless)
- **CI/CD:** GitHub Actions
- **Analytics:** Google Analytics 4
- **Documentation:** Markdown with gray-matter frontmatter

## Project Structure

```text
web/
├── app/                  # Next.js pages and API routes
│   ├── layout.tsx       # Root layout with Header/Footer
│   ├── page.tsx         # Home page
│   ├── api/             # API routes
│   ├── dashboard/       # Dashboard page
│   └── documentation/   # Documentation pages
├── components/          # React components
├── lib/                 # Utilities and helpers
├── public/              # Static assets
├── docs/                # Markdown documentation
├── package.json         # Dependencies
├── tsconfig.json        # TypeScript config
├── tailwind.config.ts   # Tailwind CSS config
├── next.config.js       # Next.js config
└── .env.example         # Environment template
```

## Development

### Setup

1. Clone the repository
2. Navigate to `web/` directory
3. Copy `.env.example` to `.env.local`
4. Run `npm install`
5. Start development: `npm run dev`

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run type-check` - Run TypeScript type checking
- `npm run lint` - Run ESLint linting

## Deployment

### Vercel (Recommended)

See [../docs/DEPLOYMENT.md](../docs/DEPLOYMENT.md) for:

- Prerequisites and setup
- Step-by-step deployment guide
- GitHub Actions CI/CD integration
- Monitoring and troubleshooting

### Environment Variables

Copy `.env.example` to `.env.local` and configure:

```bash
NEXT_PUBLIC_API_URL=http://localhost:3000/api
NEXT_PUBLIC_GITHUB_REPO=agent-jumbo-deploy/agent-jumbo
NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX
NEXT_PUBLIC_URL=http://localhost:3000
```

## CI/CD Pipeline

Automated workflows trigger on push to main:

1. **web-build.yml** - Tests on Node 18.x and 20.x
2. **web-deploy.yml** - Deploys to Vercel on success
3. **web-docs-check.yml** - Validates documentation

See [../.github/workflows/](../.github/workflows/) for details.

## Team

[Your team information]

## License

Apache License 2.0 - See [../LICENSE](../LICENSE) file for details

## Support

- **Documentation:** [In-app docs](https://agent-jumbo.vercel.app/documentation)
- **Issues:** [GitHub Issues](https://github.com/agent-jumbo-deploy/agent-jumbo/issues)
- **Discussions:** [GitHub Discussions](https://github.com/agent-jumbo-deploy/agent-jumbo/discussions)

---

**Status:** Production Ready
**Version:** 1.0.0
**Last Updated:** 2026-02-01
