"""
Analytics ROI Calculator Tool

Converted from Mahoosuc OS /analytics:roi-calculator command to native Agent Zero tool.
Calculates Return on Investment with comprehensive financial metrics.

Source: .claude/commands/analytics/roi-calculator.md
"""

from python.helpers.tool import Response, Tool


class AnalyticsROICalculator(Tool):
    async def execute(self, **kwargs):
        """
        Calculate ROI and related financial metrics

        Args (from self.args):
            investment: Initial investment amount (required)
            revenue: Total revenue generated (required)
            costs: Additional operating costs (optional, default: 0)
            period: Time period in months (optional, default: 12)

        Returns:
            Response with ROI calculation and financial analysis
        """
        # Get parameters
        investment_str = self.args.get("investment", "")
        revenue_str = self.args.get("revenue", "")
        costs_str = self.args.get("costs", "0")
        period_str = self.args.get("period", "12")

        # Validate required parameters
        if not investment_str:
            return Response(
                message="Error: investment parameter is required. "
                'Example: {"investment": "50000", "revenue": "75000"}',
                break_loop=False,
            )

        if not revenue_str:
            return Response(
                message="Error: revenue parameter is required. " 'Example: {"investment": "50000", "revenue": "75000"}',
                break_loop=False,
            )

        # Parse and validate numeric inputs
        try:
            investment = float(investment_str)
            revenue = float(revenue_str)
            costs = float(costs_str)
            period = int(period_str)
        except ValueError as e:
            return Response(
                message=f"Error: Invalid numeric input. All values must be numbers. {e!s}", break_loop=False
            )

        # Validate positive values
        if investment <= 0:
            return Response(message="Error: investment must be greater than 0", break_loop=False)

        # Calculate metrics
        net_profit = revenue - investment - costs
        roi_percentage = (net_profit / investment) * 100
        monthly_roi = roi_percentage / period if period > 0 else roi_percentage
        payback_period = (investment / (revenue / period)) if revenue > 0 else float("inf")

        # Generate report
        report = self._generate_roi_report(
            investment, revenue, costs, period, net_profit, roi_percentage, monthly_roi, payback_period
        )

        return Response(message=report, break_loop=False)

    def _generate_roi_report(
        self,
        investment: float,
        revenue: float,
        costs: float,
        period: int,
        net_profit: float,
        roi_percentage: float,
        monthly_roi: float,
        payback_period: float,
    ) -> str:
        """Generate comprehensive ROI analysis report"""
        lines = []

        lines.append("# ROI Analysis Report")
        lines.append("")

        lines.append("## Input Parameters")
        lines.append("")
        lines.append(f"- **Initial Investment**: ${investment:,.2f}")
        lines.append(f"- **Total Revenue**: ${revenue:,.2f}")
        lines.append(f"- **Operating Costs**: ${costs:,.2f}")
        lines.append(f"- **Analysis Period**: {period} months")
        lines.append("")

        lines.append("## Financial Metrics")
        lines.append("")
        lines.append(f"- **Net Profit**: ${net_profit:,.2f}")
        lines.append(f"- **ROI**: {roi_percentage:.2f}%")
        lines.append(f"- **Monthly ROI**: {monthly_roi:.2f}%")

        if payback_period != float("inf"):
            lines.append(f"- **Payback Period**: {payback_period:.1f} months")
        else:
            lines.append("- **Payback Period**: Not achievable (revenue too low)")

        lines.append("")

        lines.append("## Performance Assessment")
        lines.append("")

        if roi_percentage > 50:
            assessment = "Excellent - Well above average returns"
        elif roi_percentage > 25:
            assessment = "Good - Above average returns"
        elif roi_percentage > 0:
            assessment = "Positive - Breaking even or modest returns"
        else:
            assessment = "Negative - Investment not recovering costs"

        lines.append(f"**Assessment**: {assessment}")
        lines.append("")

        lines.append("## Breakdown")
        lines.append("")
        lines.append(f"Total Revenue: ${revenue:,.2f}")
        lines.append(f"- Initial Investment: ${investment:,.2f}")
        lines.append(f"- Operating Costs: ${costs:,.2f}")
        lines.append(f"= Net Profit: ${net_profit:,.2f}")
        lines.append("")
        lines.append("ROI = (Net Profit / Investment) × 100")
        lines.append(f"ROI = (${net_profit:,.2f} / ${investment:,.2f}) × 100 = {roi_percentage:.2f}%")
        lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("*Generated by Analytics ROI Calculator (converted from Mahoosuc OS)*")

        return "\n".join(lines)
