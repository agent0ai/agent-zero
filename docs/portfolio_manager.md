# Portfolio Manager

The Portfolio Manager is a comprehensive tool for organizing, analyzing, and commercializing your code projects. It's designed for developers and AI Solution Architects who have built multiple projects and want to sell them.

## Features

- **Project Discovery**: Automatically scan folders to discover and catalog projects
- **Quality Analysis**: Analyze projects for sale-readiness with detailed scoring
- **Product Management**: Create product listings with pricing tiers
- **Sales Pipeline**: Track sales opportunities from lead to closed
- **Export**: Generate catalogs for marketing and sales

## Quick Start

### 1. Scan Your Projects

Point Agent Jumbo to your projects folder:

```
Scan my projects folder at ~/projects for portfolio
```

### 2. Review Sale Readiness

Check which projects are ready to sell:

```
Show me my portfolio dashboard
```

### 3. Improve Projects

Get recommendations for improving a project:

```
Analyze project at ~/projects/my-tool for sale readiness
```

### 4. Create Products

Convert projects to products:

```
Create a product from project ID 1
```

### 5. Track Sales

Add leads and track your sales pipeline:

```
Add Acme Corp as a lead for product 1 with deal value $499
```

## Database Location

Portfolio data is stored at `/a0/data/portfolio.db` (persisted across container restarts).

## Sale Readiness Score

Projects are scored 0-100% based on:

| Factor | Weight | What We Check |
|--------|--------|---------------|
| README | 25% | Description, installation, usage, examples |
| Tests | 20% | Test files, coverage configuration |
| Docs | 20% | API docs, guides, examples folder |
| License | 15% | LICENSE or LICENSE.md file |
| CI/CD | 10% | GitHub Actions, CircleCI, etc. |
| Quality | 10% | Linting config, formatting |

## Actions Reference

| Action | Description |
|--------|-------------|
| `scan` | Scan folder for projects |
| `list` | List all projects |
| `get` | Get project details |
| `add` | Add project manually |
| `update` | Update project info |
| `analyze` | Analyze project quality |
| `export` | Export catalog |
| `search` | Search projects |
| `dashboard` | Portfolio overview |
| `create_product` | Create product from project |
| `pricing` | Manage pricing tiers |
| `pipeline` | Manage sales pipeline |

## Example Workflow

1. **Scan**: Discover all projects
2. **Analyze**: Identify what needs improvement
3. **Improve**: Add README, tests, license
4. **Re-scan**: Update sale-readiness scores
5. **Create Products**: List ready projects for sale
6. **Set Pricing**: Add pricing tiers
7. **Track Sales**: Manage your pipeline
8. **Export**: Generate catalogs for marketing

## Integration

Works with:

- **Diagram Tool**: Visualize portfolio structure
- **Business X-Ray**: Analyze revenue opportunities
