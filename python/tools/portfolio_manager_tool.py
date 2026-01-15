"""
Portfolio Manager Tool
Manages code projects portfolio for organization and sales
"""

from python.helpers.tool import Tool, Response
import json
import os
from pathlib import Path
import sys

# Add instruments path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "instruments" / "custom"))


class PortfolioManager(Tool):
    
    async def execute(self, **kwargs):
        """
        Execute portfolio management operations
        
        Args:
            action (str): Action to perform - 'scan', 'list', 'get', 'add', 'update', 
                          'analyze', 'export', 'search', 'pipeline', 'dashboard'
            folder_path (str): Path to folder for scanning (for 'scan' action)
            project_id (int): Project ID for get/update actions
            product_id (int): Product ID for product actions
            query (str): Search query
            filters (dict): Filter criteria for list actions
            data (dict): Data for add/update actions
            output_dir (str): Output directory for exports
        """
        
        from portfolio_manager.portfolio_manager import PortfolioManager as PM
        from portfolio_manager.portfolio_db import PortfolioDatabase as PortfolioDB
        
        action = kwargs.get("action", "list")
        output_dir = kwargs.get("output_dir", "/a0/data/portfolio_exports")
        
        try:
            pm = PM()
            db = PortfolioDB()
            
            if action == "scan":
                return await self._scan_folder(pm, kwargs.get("folder_path"))
            
            elif action == "list":
                return await self._list_projects(db, kwargs.get("filters", {}))
            
            elif action == "get":
                return await self._get_project(pm, kwargs.get("project_id"))
            
            elif action == "add":
                return await self._add_project(db, kwargs.get("data", {}))
            
            elif action == "update":
                return await self._update_project(db, kwargs.get("project_id"), kwargs.get("data", {}))
            
            elif action == "analyze":
                return await self._analyze_project(pm, kwargs.get("folder_path") or kwargs.get("project_id"))
            
            elif action == "export":
                return await self._export_catalog(pm, output_dir, kwargs.get("format", "markdown"))
            
            elif action == "search":
                return await self._search_projects(db, kwargs.get("query", ""))
            
            elif action == "pipeline":
                return await self._manage_pipeline(db, kwargs.get("data", {}))
            
            elif action == "dashboard":
                return await self._get_dashboard(pm)
            
            elif action == "create_product":
                return await self._create_product(pm, kwargs.get("project_id"))
            
            elif action == "pricing":
                return await self._manage_pricing(db, kwargs.get("product_id"), kwargs.get("data", {}))
            
            else:
                return Response(
                    message=f"Unknown action: {action}. Valid actions: scan, list, get, add, update, analyze, export, search, pipeline, dashboard, create_product, pricing",
                    break_loop=False
                )
        
        except Exception as e:
            return Response(
                message=f"Portfolio Manager error: {str(e)}",
                break_loop=False
            )
    
    async def _scan_folder(self, pm, folder_path: str) -> Response:
        """Scan a folder for projects"""
        if not folder_path:
            return Response(
                message="Error: folder_path is required for scan action",
                break_loop=False
            )
        
        if not os.path.exists(folder_path):
            return Response(
                message=f"Error: Folder not found: {folder_path}",
                break_loop=False
            )
        
        projects = pm.scan_folder(folder_path)
        
        if not projects:
            return Response(
                message=f"No projects found in {folder_path}",
                break_loop=False
            )
        
        # Format results
        result_lines = [f"**Scanned {len(projects)} projects from {folder_path}**\n"]
        
        for proj in projects:
            sale_ready = proj.get("sale_readiness", 0)
            status_emoji = "🟢" if sale_ready >= 70 else "🟡" if sale_ready >= 40 else "🔴"
            
            result_lines.append(f"""
### {status_emoji} {proj['name']}
- **Language**: {proj.get('language', 'Unknown')}
- **Path**: `{proj['path']}`
- **Sale Readiness**: {sale_ready}%
- **Has README**: {'✅' if proj.get('has_readme') else '❌'}
- **Has Tests**: {'✅' if proj.get('has_tests') else '❌'}
- **Has License**: {'✅' if proj.get('has_license') else '❌'}
""")
        
        return Response(
            message="\n".join(result_lines),
            break_loop=False
        )
    
    async def _list_projects(self, db, filters: dict) -> Response:
        """List all projects with optional filters"""
        projects = db.get_projects(
            language=filters.get("language"),
            status=filters.get("status"),
            min_sale_readiness=filters.get("min_sale_readiness")
        )
        
        if not projects:
            return Response(
                message="No projects found matching criteria",
                break_loop=False
            )
        
        # Group by status
        by_status = {}
        for p in projects:
            status = p.get("status", "draft")
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(p)
        
        lines = [f"**Portfolio: {len(projects)} Projects**\n"]
        
        for status, projs in sorted(by_status.items()):
            lines.append(f"\n### {status.title()} ({len(projs)})")
            for p in projs:
                sale_emoji = "🟢" if p.get("sale_readiness", 0) >= 70 else "🟡" if p.get("sale_readiness", 0) >= 40 else "🔴"
                lines.append(f"- {sale_emoji} **{p['name']}** ({p.get('language', 'N/A')}) - {p.get('sale_readiness', 0)}% ready")
        
        return Response(message="\n".join(lines), break_loop=False)
    
    async def _get_project(self, pm, project_id: int) -> Response:
        """Get detailed project information"""
        if not project_id:
            return Response(message="Error: project_id is required", break_loop=False)
        
        project = pm.db.get_project(project_id)
        if not project:
            return Response(message=f"Project {project_id} not found", break_loop=False)
        
        # Get products linked to this project
        products = pm.db.get_products(project_id=project_id)
        
        detail = f"""
## {project['name']}

**Basic Info:**
- **ID**: {project['id']}
- **Path**: `{project['path']}`
- **Language**: {project.get('language', 'Unknown')}
- **Status**: {project.get('status', 'draft')}
- **Sale Readiness**: {project.get('sale_readiness', 0)}%

**Quality Metrics:**
- README Quality: {project.get('readme_quality', 0)}%
- Test Coverage: {project.get('test_coverage', 0)}%
- Has License: {'✅' if project.get('has_license') else '❌'}
- Has CI/CD: {'✅' if project.get('has_ci_cd') else '❌'}

**Description:**
{project.get('description', 'No description')}

**Tags:** {project.get('tags', 'None')}
"""
        
        if products:
            detail += "\n**Products:**\n"
            for prod in products:
                detail += f"- {prod['name']} - ${prod.get('base_price', 0):.2f}\n"
        
        return Response(message=detail, break_loop=False)
    
    async def _add_project(self, db, data: dict) -> Response:
        """Add a project manually"""
        required = ["name", "path"]
        missing = [f for f in required if f not in data]
        if missing:
            return Response(
                message=f"Error: Missing required fields: {', '.join(missing)}",
                break_loop=False
            )
        
        project_id = db.add_project(**data)
        return Response(
            message=f"✅ Project added with ID: {project_id}",
            break_loop=False
        )
    
    async def _update_project(self, db, project_id: int, data: dict) -> Response:
        """Update project information"""
        if not project_id:
            return Response(message="Error: project_id is required", break_loop=False)
        
        rows = db.update_project(project_id, **data)
        if rows:
            return Response(message=f"✅ Project {project_id} updated", break_loop=False)
        return Response(message=f"Project {project_id} not found or no changes made", break_loop=False)
    
    async def _analyze_project(self, pm, identifier) -> Response:
        """Analyze a project for sale readiness"""
        if isinstance(identifier, int):
            project = pm.db.get_project(identifier)
            if not project:
                return Response(message=f"Project {identifier} not found", break_loop=False)
            folder_path = project["path"]
        else:
            folder_path = identifier
        
        if not folder_path or not os.path.exists(folder_path):
            return Response(message=f"Error: Path not found: {folder_path}", break_loop=False)
        
        analysis = pm.analyze_project(folder_path)
        
        result = f"""
## Project Analysis: {analysis.get('name', 'Unknown')}

**Sale Readiness Score: {analysis.get('sale_readiness', 0)}%**

### Breakdown:
| Category | Score | Details |
|----------|-------|---------|
| README | {analysis.get('readme_quality', 0)}% | {analysis.get('readme_notes', 'N/A')} |
| Tests | {analysis.get('test_coverage', 0)}% | {analysis.get('test_notes', 'N/A')} |
| License | {'100' if analysis.get('has_license') else '0'}% | {'Present' if analysis.get('has_license') else 'Missing'} |
| Documentation | {analysis.get('docs_quality', 0)}% | {analysis.get('docs_notes', 'N/A')} |
| CI/CD | {'100' if analysis.get('has_ci_cd') else '0'}% | {'Configured' if analysis.get('has_ci_cd') else 'Not found'} |

### Recommendations:
"""
        
        for rec in analysis.get('recommendations', ['No recommendations']):
            result += f"- {rec}\n"
        
        return Response(message=result, break_loop=False)
    
    async def _export_catalog(self, pm, output_dir: str, format: str) -> Response:
        """Export product catalog"""
        os.makedirs(output_dir, exist_ok=True)
        
        export_path = pm.export_catalog(output_dir, format)
        
        return Response(
            message=f"✅ Catalog exported to: {export_path}",
            break_loop=False
        )
    
    async def _search_projects(self, db, query: str) -> Response:
        """Search projects"""
        if not query:
            return Response(message="Error: query is required for search", break_loop=False)
        
        results = db.search_projects(query)
        
        if not results:
            return Response(message=f"No projects found matching '{query}'", break_loop=False)
        
        lines = [f"**Search Results for '{query}': {len(results)} found**\n"]
        for p in results:
            lines.append(f"- **{p['name']}** ({p.get('language', 'N/A')}) - {p.get('path', '')}")
        
        return Response(message="\n".join(lines), break_loop=False)
    
    async def _manage_pipeline(self, db, data: dict) -> Response:
        """Manage sales pipeline"""
        action = data.get("pipeline_action", "list")
        
        if action == "list":
            pipeline = db.get_sales_pipeline()
            if not pipeline:
                return Response(message="Sales pipeline is empty", break_loop=False)
            
            lines = ["**Sales Pipeline**\n"]
            by_stage = {}
            for item in pipeline:
                stage = item.get("stage", "lead")
                if stage not in by_stage:
                    by_stage[stage] = []
                by_stage[stage].append(item)
            
            stage_order = ["lead", "qualified", "proposal", "negotiation", "closed_won", "closed_lost"]
            for stage in stage_order:
                if stage in by_stage:
                    lines.append(f"\n### {stage.replace('_', ' ').title()} ({len(by_stage[stage])})")
                    for item in by_stage[stage]:
                        lines.append(f"- {item.get('customer_name', 'Unknown')} - ${item.get('deal_value', 0):,.2f}")
            
            return Response(message="\n".join(lines), break_loop=False)
        
        elif action == "add":
            required = ["product_id", "customer_name"]
            missing = [f for f in required if f not in data]
            if missing:
                return Response(message=f"Missing required: {', '.join(missing)}", break_loop=False)
            
            sale_id = db.add_to_pipeline(**data)
            return Response(message=f"✅ Added to pipeline with ID: {sale_id}", break_loop=False)
        
        elif action == "update":
            if "sale_id" not in data:
                return Response(message="Error: sale_id required for update", break_loop=False)
            
            db.update_pipeline_stage(data["sale_id"], data.get("stage"), data.get("notes"))
            return Response(message=f"✅ Pipeline item {data['sale_id']} updated", break_loop=False)
        
        return Response(message=f"Unknown pipeline action: {action}", break_loop=False)
    
    async def _get_dashboard(self, pm) -> Response:
        """Get portfolio dashboard"""
        stats = pm.get_portfolio_stats()
        
        dashboard = f"""
## 📊 Portfolio Dashboard

### Overview
- **Total Projects**: {stats.get('total_projects', 0)}
- **Products Listed**: {stats.get('total_products', 0)}
- **Average Sale Readiness**: {stats.get('avg_sale_readiness', 0):.1f}%

### By Status
| Status | Count |
|--------|-------|
"""
        
        for status, count in stats.get('by_status', {}).items():
            dashboard += f"| {status.title()} | {count} |\n"
        
        dashboard += "\n### By Language\n| Language | Count |\n|----------|-------|\n"
        
        for lang, count in stats.get('by_language', {}).items():
            dashboard += f"| {lang} | {count} |\n"
        
        if stats.get('pipeline_value'):
            dashboard += f"\n### Sales Pipeline\n- **Total Value**: ${stats.get('pipeline_value', 0):,.2f}\n"
        
        # Top projects ready for sale
        dashboard += "\n### 🟢 Top Sale-Ready Projects\n"
        for proj in stats.get('top_ready', [])[:5]:
            dashboard += f"- **{proj['name']}** - {proj['sale_readiness']}% ready\n"
        
        return Response(message=dashboard, break_loop=False)
    
    async def _create_product(self, pm, project_id: int) -> Response:
        """Create a product listing from a project"""
        if not project_id:
            return Response(message="Error: project_id is required", break_loop=False)
        
        product = pm.create_product_from_project(project_id)
        
        if not product:
            return Response(message=f"Failed to create product from project {project_id}", break_loop=False)
        
        return Response(
            message=f"✅ Product created: **{product['name']}** (ID: {product['id']})\nBase Price: ${product.get('base_price', 0):.2f}",
            break_loop=False
        )
    
    async def _manage_pricing(self, db, product_id: int, data: dict) -> Response:
        """Manage product pricing tiers"""
        if not product_id:
            return Response(message="Error: product_id is required", break_loop=False)
        
        action = data.get("pricing_action", "list")
        
        if action == "list":
            tiers = db.get_pricing_tiers(product_id)
            if not tiers:
                return Response(message=f"No pricing tiers for product {product_id}", break_loop=False)
            
            lines = [f"**Pricing Tiers for Product {product_id}**\n"]
            for tier in tiers:
                lines.append(f"- **{tier['name']}**: ${tier['price']:.2f} - {tier.get('description', '')}")
            
            return Response(message="\n".join(lines), break_loop=False)
        
        elif action == "add":
            required = ["name", "price"]
            missing = [f for f in required if f not in data]
            if missing:
                return Response(message=f"Missing required: {', '.join(missing)}", break_loop=False)
            
            tier_id = db.add_pricing_tier(
                product_id=product_id,
                name=data["name"],
                price=data["price"],
                description=data.get("description", ""),
                features=data.get("features")
            )
            return Response(message=f"✅ Pricing tier added: {data['name']} at ${data['price']:.2f}", break_loop=False)
        
        return Response(message=f"Unknown pricing action: {action}", break_loop=False)
