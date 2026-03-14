"""
Sales Generator Tool for Agent Jumbo
Create customer-facing proposals, demos, ROI analyses, and business cases
"""

from python.helpers import files
from python.helpers.tool import Response, Tool


class SalesGenerator(Tool):
    """
    Agent Jumbo tool for generating sales materials.
    Creates proposals, demos, ROI calculations, case studies, and business cases.
    """

    def __init__(self, agent, name: str, method: str | None, args: dict, message: str, loop_data=None, **kwargs):
        super().__init__(agent, name, method, args, message, loop_data, **kwargs)

        # Import manager here to avoid circular imports
        from instruments.custom.sales_generator.sales_manager import SalesGeneratorManager

        # Initialize manager
        db_path = files.get_abs_path("./instruments/custom/sales_generator/data/sales_generator.db")
        self.manager = SalesGeneratorManager(db_path)

    async def execute(self, **kwargs):
        """Execute sales generator action"""

        action = self.args.get("action", "").lower()

        # Route to appropriate action handler
        action_handlers = {
            # Proposal actions
            "generate_proposal": self._generate_proposal,
            "get_proposal": self._get_proposal,
            "list_proposals": self._list_proposals,
            "update_proposal_status": self._update_proposal_status,
            # Demo actions
            "create_demo": self._create_demo,
            "get_demo": self._get_demo,
            "list_demos": self._list_demos,
            # ROI actions
            "calculate_roi": self._calculate_roi,
            "get_roi": self._get_roi,
            "list_roi": self._list_roi,
            # Case study actions
            "generate_case_study": self._generate_case_study,
            "get_case_study": self._get_case_study,
            "list_case_studies": self._list_case_studies,
            # Showcase actions
            "generate_portfolio_showcase": self._generate_portfolio_showcase,
            "get_showcase": self._get_showcase,
            "list_showcases": self._list_showcases,
            # Business case actions
            "build_business_case": self._build_business_case,
            "get_business_case": self._get_business_case,
            "list_business_cases": self._list_business_cases,
            # Comparison actions
            "create_comparison": self._create_comparison,
            "get_comparison": self._get_comparison,
            "list_comparisons": self._list_comparisons,
            # Statistics
            "get_stats": self._get_stats,
        }

        handler = action_handlers.get(action)
        if handler:
            return await handler()

        return Response(
            message=f"Unknown action: {action}. Available: {', '.join(action_handlers.keys())}", break_loop=False
        )

    # ========== Proposal Actions ==========

    async def _generate_proposal(self):
        """Generate a full proposal document"""
        title = self.args.get("title")
        customer_id = self.args.get("customer_id")
        customer_name = self.args.get("customer_name")
        solution_summary = self.args.get("solution_summary")
        items = self.args.get("items", [])
        valid_days = self.args.get("valid_days", 30)

        if not title:
            return Response(message="Error: title is required", break_loop=False)

        result = self.manager.generate_proposal(
            title=title,
            customer_id=customer_id,
            customer_name=customer_name,
            solution_summary=solution_summary,
            items=items,
            valid_days=valid_days,
        )

        lines = ["## Proposal Generated\n"]
        lines.append(f"**Proposal ID:** {result['proposal_id']}")
        lines.append(f"**Title:** {result['title']}")
        lines.append(f"**Customer:** {result['customer_name'] or 'Not specified'}")
        lines.append(f"**Total:** ${result['total']:,.2f}")
        lines.append(f"**Status:** {result['status']}")
        lines.append("")
        lines.append("### Content Preview")
        lines.append("")
        # Show first 500 chars of content
        content_preview = result["content"][:500] + "..." if len(result["content"]) > 500 else result["content"]
        lines.append(content_preview)

        return Response(message="\n".join(lines), break_loop=False)

    async def _get_proposal(self):
        """Get proposal details"""
        proposal_id = self.args.get("proposal_id")

        if not proposal_id:
            return Response(message="Error: proposal_id is required", break_loop=False)

        result = self.manager.get_proposal(proposal_id)

        if not result:
            return Response(message=f"Proposal not found: {proposal_id}", break_loop=False)

        lines = [f"## Proposal: {result['title']}\n"]
        lines.append(f"**ID:** {result['proposal_id']}")
        lines.append(f"**Customer:** {result.get('customer_name', 'N/A')}")
        lines.append(f"**Status:** {result['status']}")
        lines.append(f"**Total:** ${result.get('pricing_total', 0):,.2f}")
        lines.append(f"**Valid Until:** {result.get('valid_until', 'N/A')}")
        lines.append("")

        if result.get("items"):
            lines.append("### Line Items")
            for item in result["items"]:
                lines.append(f"- {item['name']}: ${item['total_price']:,.2f}")
        lines.append("")

        if result.get("content"):
            lines.append("### Full Content")
            lines.append(result["content"])

        return Response(message="\n".join(lines), break_loop=False)

    async def _list_proposals(self):
        """List proposals"""
        customer_id = self.args.get("customer_id")
        status = self.args.get("status")

        proposals = self.manager.list_proposals(customer_id, status)

        if not proposals:
            return Response(message="No proposals found.", break_loop=False)

        lines = ["## Proposals\n"]
        for p in proposals:
            lines.append(f"### {p['title']} (ID: {p['proposal_id']})")
            lines.append(f"- Customer: {p.get('customer_name', 'N/A')}")
            lines.append(f"- Status: {p['status']}")
            lines.append(f"- Total: ${p.get('pricing_total', 0):,.2f}")
            lines.append(f"- Created: {p['created_at']}")
            lines.append("")

        return Response(message="\n".join(lines), break_loop=False)

    async def _update_proposal_status(self):
        """Update proposal status"""
        proposal_id = self.args.get("proposal_id")
        status = self.args.get("status")

        if not proposal_id or not status:
            return Response(message="Error: proposal_id and status are required", break_loop=False)

        self.manager.update_proposal_status(proposal_id, status)

        return Response(message=f"Proposal {proposal_id} status updated to: {status}", break_loop=False)

    # ========== Demo Actions ==========

    async def _create_demo(self):
        """Create a demo specification"""
        title = self.args.get("title")
        customer_id = self.args.get("customer_id")
        customer_name = self.args.get("customer_name")
        demo_type = self.args.get("demo_type", "interactive")
        features = self.args.get("features", [])
        description = self.args.get("description")

        if not title:
            return Response(message="Error: title is required", break_loop=False)

        result = self.manager.create_demo(
            title=title,
            customer_id=customer_id,
            customer_name=customer_name,
            demo_type=demo_type,
            features=features,
            description=description,
        )

        lines = ["## Demo Created\n"]
        lines.append(f"**Demo ID:** {result['demo_id']}")
        lines.append(f"**Title:** {result['title']}")
        lines.append(f"**Type:** {result['demo_type']}")
        lines.append(f"**Features:** {result['features_count']}")
        lines.append("")
        lines.append("### Demo Script")
        lines.append(result["content"])

        return Response(message="\n".join(lines), break_loop=False)

    async def _get_demo(self):
        """Get demo details"""
        demo_id = self.args.get("demo_id")

        if not demo_id:
            return Response(message="Error: demo_id is required", break_loop=False)

        result = self.manager.get_demo(demo_id)

        if not result:
            return Response(message=f"Demo not found: {demo_id}", break_loop=False)

        return Response(message=self._format_result(result, f"Demo: {result['title']}"), break_loop=False)

    async def _list_demos(self):
        """List demos"""
        customer_id = self.args.get("customer_id")

        demos = self.manager.list_demos(customer_id)

        if not demos:
            return Response(message="No demos found.", break_loop=False)

        lines = ["## Demos\n"]
        for d in demos:
            lines.append(f"- **{d['title']}** (ID: {d['demo_id']}) - {d['demo_type']}")
            lines.append(f"  Features: {len(d.get('features', []))}, Created: {d['created_at']}")

        return Response(message="\n".join(lines), break_loop=False)

    # ========== ROI Actions ==========

    async def _calculate_roi(self):
        """Calculate ROI with projections"""
        title = self.args.get("title")
        customer_id = self.args.get("customer_id")
        customer_name = self.args.get("customer_name")
        current_costs = self.args.get("current_costs", {})
        projected_savings = self.args.get("projected_savings", {})
        implementation_cost = self.args.get("implementation_cost", 0)
        years = self.args.get("years", 3)

        if not title:
            return Response(message="Error: title is required", break_loop=False)

        result = self.manager.calculate_roi(
            title=title,
            customer_id=customer_id,
            customer_name=customer_name,
            current_costs=current_costs,
            projected_savings=projected_savings,
            implementation_cost=implementation_cost,
            years=years,
        )

        lines = [f"## ROI Analysis: {title}\n"]
        lines.append(f"**ROI ID:** {result['roi_id']}")
        lines.append("")

        lines.append("### Summary")
        summary = result["summary"]
        lines.append(f"- Annual Current Cost: ${summary['annual_current_cost']:,.2f}")
        lines.append(f"- Annual Savings: ${summary['annual_savings']:,.2f}")
        lines.append(f"- Total Investment: ${summary['total_investment']:,.2f}")
        lines.append(f"- Payback Period: {summary['payback_months']} months")
        lines.append(f"- ROI: {summary['roi_percentage']}%")
        lines.append(f"- NPV: ${summary['npv']:,.2f}")
        lines.append("")

        lines.append("### Projections")
        for scenario, data in result["projections"].items():
            lines.append(f"\n**{scenario.title()} Scenario**")
            lines.append(f"- Annual Savings: ${data['annual_savings']:,.2f}")
            lines.append(f"- Payback: {data['payback_months']} months")
            for year, vals in data["years"].items():
                status = "+" if vals["positive"] else ""
                lines.append(f"  - {year.replace('_', ' ').title()}: {status}${vals['cumulative']:,.2f}")

        return Response(message="\n".join(lines), break_loop=False)

    async def _get_roi(self):
        """Get ROI calculation"""
        roi_id = self.args.get("roi_id")

        if not roi_id:
            return Response(message="Error: roi_id is required", break_loop=False)

        result = self.manager.get_roi_calculation(roi_id)

        if not result:
            return Response(message=f"ROI calculation not found: {roi_id}", break_loop=False)

        return Response(message=self._format_result(result, f"ROI: {result['title']}"), break_loop=False)

    async def _list_roi(self):
        """List ROI calculations"""
        customer_id = self.args.get("customer_id")

        calculations = self.manager.list_roi_calculations(customer_id)

        if not calculations:
            return Response(message="No ROI calculations found.", break_loop=False)

        lines = ["## ROI Calculations\n"]
        for c in calculations:
            lines.append(f"- **{c['title']}** (ID: {c['roi_id']})")
            if c.get("roi_percentage"):
                lines.append(f"  ROI: {c['roi_percentage']}%, Payback: {c.get('payback_months', 'N/A')} months")

        return Response(message="\n".join(lines), break_loop=False)

    # ========== Case Study Actions ==========

    async def _generate_case_study(self):
        """Generate a case study"""
        project_name = self.args.get("project_name")
        customer_id = self.args.get("customer_id")
        customer_name = self.args.get("customer_name")
        industry = self.args.get("industry")
        challenge = self.args.get("challenge")
        solution = self.args.get("solution")
        results = self.args.get("results")
        metrics = self.args.get("metrics", {})
        testimonial = self.args.get("testimonial")

        if not project_name:
            return Response(message="Error: project_name is required", break_loop=False)

        result = self.manager.generate_case_study(
            project_name=project_name,
            customer_id=customer_id,
            customer_name=customer_name,
            industry=industry,
            challenge=challenge,
            solution=solution,
            results=results,
            metrics=metrics,
            testimonial=testimonial,
        )

        lines = ["## Case Study Generated\n"]
        lines.append(f"**Case Study ID:** {result['case_study_id']}")
        lines.append(f"**Project:** {result['project_name']}")
        lines.append(f"**Industry:** {result.get('industry', 'N/A')}")
        lines.append("")
        lines.append("### Content")
        lines.append(result["content"])

        return Response(message="\n".join(lines), break_loop=False)

    async def _get_case_study(self):
        """Get case study"""
        case_study_id = self.args.get("case_study_id")

        if not case_study_id:
            return Response(message="Error: case_study_id is required", break_loop=False)

        result = self.manager.get_case_study(case_study_id)

        if not result:
            return Response(message=f"Case study not found: {case_study_id}", break_loop=False)

        return Response(message=self._format_result(result, f"Case Study: {result['project_name']}"), break_loop=False)

    async def _list_case_studies(self):
        """List case studies"""
        industry = self.args.get("industry")
        status = self.args.get("status")

        case_studies = self.manager.list_case_studies(industry, status)

        if not case_studies:
            return Response(message="No case studies found.", break_loop=False)

        lines = ["## Case Studies\n"]
        for cs in case_studies:
            lines.append(f"- **{cs['project_name']}** (ID: {cs['case_study_id']})")
            lines.append(f"  Industry: {cs.get('industry', 'N/A')}, Status: {cs['status']}")

        return Response(message="\n".join(lines), break_loop=False)

    # ========== Showcase Actions ==========

    async def _generate_portfolio_showcase(self):
        """Generate a portfolio showcase"""
        title = self.args.get("title")
        description = self.args.get("description")
        projects = self.args.get("projects", [])
        target_industry = self.args.get("target_industry")

        if not title:
            return Response(message="Error: title is required", break_loop=False)

        result = self.manager.generate_portfolio_showcase(
            title=title, description=description, projects=projects, target_industry=target_industry
        )

        lines = ["## Portfolio Showcase Generated\n"]
        lines.append(f"**Showcase ID:** {result['showcase_id']}")
        lines.append(f"**Title:** {result['title']}")
        lines.append(f"**Projects Featured:** {result['projects_count']}")
        lines.append("")
        lines.append("### Content")
        lines.append(result["content"])

        return Response(message="\n".join(lines), break_loop=False)

    async def _get_showcase(self):
        """Get showcase"""
        showcase_id = self.args.get("showcase_id")

        if not showcase_id:
            return Response(message="Error: showcase_id is required", break_loop=False)

        result = self.manager.get_showcase(showcase_id)

        if not result:
            return Response(message=f"Showcase not found: {showcase_id}", break_loop=False)

        return Response(message=self._format_result(result, f"Showcase: {result['title']}"), break_loop=False)

    async def _list_showcases(self):
        """List showcases"""
        target_industry = self.args.get("target_industry")

        showcases = self.manager.list_showcases(target_industry)

        if not showcases:
            return Response(message="No showcases found.", break_loop=False)

        lines = ["## Portfolio Showcases\n"]
        for s in showcases:
            lines.append(f"- **{s['title']}** (ID: {s['showcase_id']})")
            lines.append(f"  Projects: {len(s.get('projects', []))}, Industry: {s.get('target_industry', 'General')}")

        return Response(message="\n".join(lines), break_loop=False)

    # ========== Business Case Actions ==========

    async def _build_business_case(self):
        """Build a comprehensive business case"""
        title = self.args.get("title")
        customer_id = self.args.get("customer_id")
        customer_name = self.args.get("customer_name")
        problem_statement = self.args.get("problem_statement")
        proposed_solution = self.args.get("proposed_solution")
        benefits = self.args.get("benefits", [])
        risks = self.args.get("risks", [])
        timeline = self.args.get("timeline")
        investment_required = self.args.get("investment_required")
        recommendation = self.args.get("recommendation")

        if not title:
            return Response(message="Error: title is required", break_loop=False)

        result = self.manager.build_business_case(
            title=title,
            customer_id=customer_id,
            customer_name=customer_name,
            problem_statement=problem_statement,
            proposed_solution=proposed_solution,
            benefits=benefits,
            risks=risks,
            timeline=timeline,
            investment_required=investment_required,
            recommendation=recommendation,
        )

        lines = ["## Business Case Created\n"]
        lines.append(f"**Case ID:** {result['case_id']}")
        lines.append(f"**Title:** {result['title']}")
        lines.append(f"**Benefits Identified:** {result['benefits_count']}")
        lines.append(f"**Risks Identified:** {result['risks_count']}")
        if result.get("investment_required"):
            lines.append(f"**Investment Required:** ${result['investment_required']:,.2f}")
        lines.append("")
        lines.append("### Executive Summary")
        lines.append(result["executive_summary"])

        return Response(message="\n".join(lines), break_loop=False)

    async def _get_business_case(self):
        """Get business case"""
        case_id = self.args.get("case_id")

        if not case_id:
            return Response(message="Error: case_id is required", break_loop=False)

        result = self.manager.get_business_case(case_id)

        if not result:
            return Response(message=f"Business case not found: {case_id}", break_loop=False)

        return Response(message=self._format_result(result, f"Business Case: {result['title']}"), break_loop=False)

    async def _list_business_cases(self):
        """List business cases"""
        customer_id = self.args.get("customer_id")

        cases = self.manager.list_business_cases(customer_id)

        if not cases:
            return Response(message="No business cases found.", break_loop=False)

        lines = ["## Business Cases\n"]
        for c in cases:
            lines.append(f"- **{c['title']}** (ID: {c['case_id']})")
            lines.append(f"  Status: {c['status']}, Created: {c['created_at']}")

        return Response(message="\n".join(lines), break_loop=False)

    # ========== Comparison Actions ==========

    async def _create_comparison(self):
        """Create competitive comparison"""
        title = self.args.get("title")
        our_solution = self.args.get("our_solution")
        competitors = self.args.get("competitors", [])
        criteria = self.args.get("criteria", [])

        if not title or not our_solution:
            return Response(message="Error: title and our_solution are required", break_loop=False)

        result = self.manager.create_comparison(
            title=title, our_solution=our_solution, competitors=competitors, criteria=criteria
        )

        lines = ["## Comparison Created\n"]
        lines.append(f"**Comparison ID:** {result['comparison_id']}")
        lines.append(f"**Title:** {result['title']}")
        lines.append(f"**Competitors:** {result['competitors_count']}")
        lines.append(f"**Criteria:** {result['criteria_count']}")
        lines.append("")
        lines.append("### Analysis")
        lines.append(result["analysis"])

        return Response(message="\n".join(lines), break_loop=False)

    async def _get_comparison(self):
        """Get comparison"""
        comparison_id = self.args.get("comparison_id")

        if not comparison_id:
            return Response(message="Error: comparison_id is required", break_loop=False)

        result = self.manager.get_comparison(comparison_id)

        if not result:
            return Response(message=f"Comparison not found: {comparison_id}", break_loop=False)

        return Response(message=self._format_result(result, f"Comparison: {result['title']}"), break_loop=False)

    async def _list_comparisons(self):
        """List comparisons"""
        comparisons = self.manager.list_comparisons()

        if not comparisons:
            return Response(message="No comparisons found.", break_loop=False)

        lines = ["## Competitive Comparisons\n"]
        for c in comparisons:
            lines.append(f"- **{c['title']}** (ID: {c['comparison_id']})")
            lines.append(f"  Our Solution: {c['our_solution']}, Competitors: {len(c.get('competitors', []))}")

        return Response(message="\n".join(lines), break_loop=False)

    # ========== Statistics ==========

    async def _get_stats(self):
        """Get overall statistics"""
        stats = self.manager.get_stats()

        lines = ["## Sales Generator Statistics\n"]

        lines.append("### Totals")
        for key, value in stats["totals"].items():
            lines.append(f"- {key.replace('_', ' ').title()}: {value}")

        if stats.get("proposal_status"):
            lines.append("")
            lines.append("### Proposal Status Breakdown")
            for status, count in stats["proposal_status"].items():
                lines.append(f"- {status}: {count}")

        return Response(message="\n".join(lines), break_loop=False)

    # ========== Helpers ==========

    def _format_result(self, data: dict, title: str) -> str:
        """Format result dictionary as readable output"""
        lines = [f"## {title}\n"]

        for key, value in data.items():
            if key in ["content", "analysis"]:
                lines.append(f"\n### {key.title()}")
                lines.append(str(value))
            elif isinstance(value, dict):
                lines.append(f"**{key}:**")
                for k, v in value.items():
                    lines.append(f"  - {k}: {v}")
            elif isinstance(value, list):
                lines.append(f"**{key}:** ({len(value)} items)")
                for item in value[:5]:
                    if isinstance(item, dict):
                        lines.append(f"  - {item.get('name', item)}")
                    else:
                        lines.append(f"  - {item}")
                if len(value) > 5:
                    lines.append(f"  ... and {len(value) - 5} more")
            else:
                lines.append(f"**{key}:** {value}")

        return "\n".join(lines)
