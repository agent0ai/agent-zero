"""
Business X-Ray Tool
Comprehensive business analysis and optimization tool
"""

from python.helpers.tool import Tool, Response
from python.helpers import files
import subprocess
import json
import os
from pathlib import Path


class BusinessXRay(Tool):
    
    async def execute(self, **kwargs):
        """
        Execute business analysis
        
        Args:
            analysis_type (str): Type of analysis - 'comprehensive', 'health', 'time', 'automation', 'revenue', 'balance'
            business_name (str): Name of the business to analyze
            output_dir (str): Directory to save reports (optional)
            data (dict): Input data for specific analysis type (optional)
        """
        
        analysis_type = kwargs.get("analysis_type", "comprehensive")
        business_name = kwargs.get("business_name", "My Business")
        output_dir = kwargs.get("output_dir", "/tmp/business_xray")
        data = kwargs.get("data", {})
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            if analysis_type == "comprehensive":
                return await self._run_comprehensive_analysis(business_name, output_dir)
            
            elif analysis_type == "health":
                return await self._analyze_business_health(business_name, output_dir, data)
            
            elif analysis_type == "time":
                return await self._audit_time_usage(business_name, output_dir, data)
            
            elif analysis_type == "automation":
                return await self._identify_automation(business_name, output_dir, data)
            
            elif analysis_type == "revenue":
                return await self._scan_revenue_opportunities(business_name, output_dir, data)
            
            elif analysis_type == "balance":
                return await self._analyze_life_balance(business_name, output_dir, data)
            
            else:
                return Response(
                    message=f"Unknown analysis type: {analysis_type}",
                    break_loop=False
                )
        
        except Exception as e:
            return Response(
                message=f"Business X-Ray analysis failed: {str(e)}",
                break_loop=False
            )
    
    async def _run_comprehensive_analysis(self, business_name: str, output_dir: str):
        """Run comprehensive business analysis"""
        
        script_path = Path(__file__).parent.parent.parent / "instruments" / "custom" / "business_xray" / "comprehensive_xray.py"
        
        if not script_path.exists():
            return Response(
                message=f"Business X-Ray script not found at {script_path}",
                break_loop=False
            )
        
        # Run comprehensive analysis script
        # Note: This requires interactive input - for agent use, we'll provide defaults
        result = subprocess.run(
            [
                "python3",
                str(script_path),
                "--business-name", business_name,
                "--output-dir", output_dir,
                "--quick"  # Use defaults for agent execution
            ],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            return Response(
                message=f"Comprehensive analysis failed:\n{result.stderr}",
                break_loop=False
            )
        
        # Read generated reports
        reports = self._collect_reports(output_dir)
        
        message = f"""
**Business X-Ray Comprehensive Analysis Complete**

Business: {business_name}
Reports saved to: {output_dir}

{reports.get('executive_summary', 'No summary available')}

**Generated Reports:**
- Dashboard: {output_dir}/dashboard.md
- Business Health: {output_dir}/business_health.mmd
- Time Audit: {output_dir}/time_audit.mmd
- Automation Opportunities: {output_dir}/automation_opportunities.md
- Revenue Opportunities: {output_dir}/revenue_opportunities.mmd
- Life Balance: {output_dir}/life_balance.md

View the dashboard for a complete overview.
"""
        
        return Response(message=message, break_loop=False)
    
    async def _analyze_business_health(self, business_name: str, output_dir: str, data: dict):
        """Analyze business health metrics"""
        
        # Extract metrics from data or use defaults
        revenue = data.get('monthly_revenue', 10000)
        growth_rate = data.get('growth_rate', 5)
        profit_margin = data.get('profit_margin', 20)
        total_customers = data.get('total_customers', 100)
        cac = data.get('cac', 100)
        ltv = data.get('ltv', 1000)
        
        # Calculate health score
        health_score = self._calculate_health_score(revenue, growth_rate, profit_margin, ltv/cac if cac > 0 else 0)
        
        # Generate Mermaid diagram
        diagram = f"""```mermaid
graph TB
    subgraph "Revenue Health"
        R1[Monthly Revenue: ${revenue:,.0f}]
        R2[Growth Rate: {growth_rate}%]
    end
    subgraph "Profitability"
        P1[Profit Margin: {profit_margin}%]
    end
    subgraph "Customers"
        C1[Total: {total_customers}]
        C2[LTV/CAC: {ltv/cac if cac > 0 else 0:.1f}x]
    end
    
    R1 --> Score[Health Score: {health_score}/100]
    P1 --> Score
    C2 --> Score
    
    style Score fill:#e1f5ff
```"""
        
        # Save diagram
        diagram_file = Path(output_dir) / "business_health.mmd"
        with open(diagram_file, 'w') as f:
            f.write(diagram)
        
        message = f"""
**Business Health Analysis: {business_name}**

{diagram}

**Overall Health Score: {health_score}/100**

Key Metrics:
- Monthly Revenue: ${revenue:,.2f}
- Growth Rate: {growth_rate}%
- Profit Margin: {profit_margin}%
- LTV/CAC Ratio: {ltv/cac if cac > 0 else 0:.1f}x

Recommendations:
{self._get_health_recommendations(health_score, growth_rate, profit_margin, ltv/cac if cac > 0 else 0)}
"""
        
        return Response(message=message, break_loop=False)
    
    async def _audit_time_usage(self, business_name: str, output_dir: str, data: dict):
        """Audit time allocation"""
        
        deep_work = data.get('deep_work_hours', 20)
        meetings = data.get('meeting_hours', 10)
        email = data.get('email_hours', 10)
        shallow = data.get('shallow_work_hours', 10)
        personal = data.get('personal_hours', 20)
        
        total_work = deep_work + meetings + email + shallow
        efficiency_score = round((deep_work / total_work * 100) if total_work > 0 else 0, 1)
        
        diagram = f"""```mermaid
pie title Weekly Time Distribution
    "Deep Work ({deep_work}h)" : {deep_work}
    "Meetings ({meetings}h)" : {meetings}
    "Email/Admin ({email}h)" : {email}
    "Shallow Work ({shallow}h)" : {shallow}
    "Personal ({personal}h)" : {personal}
```

**Time Efficiency Score: {efficiency_score}%**"""
        
        diagram_file = Path(output_dir) / "time_audit.mmd"
        with open(diagram_file, 'w') as f:
            f.write(diagram)
        
        message = f"""
**Time Audit: {business_name}**

{diagram}

Recommendations:
{self._get_time_recommendations(efficiency_score, deep_work, meetings)}
"""
        
        return Response(message=message, break_loop=False)
    
    async def _identify_automation(self, business_name: str, output_dir: str, data: dict):
        """Identify automation opportunities"""
        
        # Default common automation opportunities
        opportunities = data.get('opportunities', [
            {"task": "Invoice generation", "hours_week": 8, "potential": 95},
            {"task": "Email responses", "hours_week": 6, "potential": 70},
            {"task": "Data entry", "hours_week": 4, "potential": 90},
            {"task": "Report generation", "hours_week": 4, "potential": 85},
            {"task": "Social media posting", "hours_week": 5, "potential": 80},
        ])
        
        # Calculate savings
        hourly_rate = data.get('hourly_rate', 50)
        results = []
        
        for opp in opportunities:
            hours = opp['hours_week']
            potential = opp['potential']
            weekly_cost = hours * hourly_rate
            monthly_savings = weekly_cost * 4 * (potential / 100)
            annual_savings = monthly_savings * 12
            
            results.append({
                "task": opp['task'],
                "hours_week": hours,
                "potential": potential,
                "annual_savings": annual_savings
            })
        
        # Sort by savings
        results.sort(key=lambda x: x['annual_savings'], reverse=True)
        
        # Generate table
        table = "| Priority | Task | Hours/Week | Automation Potential | Annual Savings |\n"
        table += "|----------|------|------------|---------------------|----------------|\n"
        
        for i, r in enumerate(results[:10], 1):
            table += f"| {i} | {r['task']} | {r['hours_week']} | {r['potential']}% | ${r['annual_savings']:,.0f} |\n"
        
        total_savings = sum(r['annual_savings'] for r in results)
        
        message = f"""
**Automation Opportunities: {business_name}**

{table}

**Total Potential Savings: ${total_savings:,.2f}/year**

Top 3 Quick Wins:
1. {results[0]['task']} - ${results[0]['annual_savings']:,.0f}/year
2. {results[1]['task']} - ${results[1]['annual_savings']:,.0f}/year
3. {results[2]['task']} - ${results[2]['annual_savings']:,.0f}/year

Next Steps:
- Start with highest ROI automation
- Evaluate no-code/low-code solutions
- Calculate implementation costs
- Create automation roadmap
"""
        
        # Save to file
        report_file = Path(output_dir) / "automation_opportunities.md"
        with open(report_file, 'w') as f:
            f.write(message)
        
        return Response(message=message, break_loop=False)
    
    async def _scan_revenue_opportunities(self, business_name: str, output_dir: str, data: dict):
        """Identify revenue growth opportunities"""
        
        current_revenue = data.get('current_annual_revenue', 120000)
        
        opportunities = data.get('opportunities', [
            {"name": "Price increase", "potential": 12000, "difficulty": 3, "months": 1},
            {"name": "Upsell existing customers", "potential": 24000, "difficulty": 4, "months": 3},
            {"name": "New market segment", "potential": 36000, "difficulty": 7, "months": 6},
            {"name": "Subscription model", "potential": 48000, "difficulty": 6, "months": 4},
            {"name": "Digital products", "potential": 18000, "difficulty": 5, "months": 2},
        ])
        
        # Sort by potential
        opportunities.sort(key=lambda x: x['potential'], reverse=True)
        
        # Generate diagram
        diagram = f"""```mermaid
graph LR
    Current[Current Revenue<br/>${current_revenue:,.0f}/year]
"""
        
        for i, opp in enumerate(opportunities[:5], 1):
            diagram += f"    Current --> O{i}[{opp['name']}<br/>+${opp['potential']:,.0f}]\n"
        
        total_potential = sum(opp['potential'] for opp in opportunities)
        target = current_revenue + total_potential
        
        for i in range(1, len(opportunities[:5]) + 1):
            diagram += f"    O{i} --> Target\n"
        
        diagram += f"    Target[Target Revenue<br/>${target:,.0f}/year]\n```"
        
        diagram_file = Path(output_dir) / "revenue_opportunities.mmd"
        with open(diagram_file, 'w') as f:
            f.write(diagram)
        
        # Generate table
        table = "\n| Opportunity | Revenue Potential | Difficulty (1-10) | Timeframe |\n"
        table += "|-------------|-------------------|-------------------|------------|\n"
        
        for opp in opportunities:
            table += f"| {opp['name']} | +${opp['potential']:,.0f}/year | {opp['difficulty']}/10 | {opp['months']} months |\n"
        
        message = f"""
**Revenue Growth Opportunities: {business_name}**

{diagram}

{table}

**Total Revenue Potential: +${total_potential:,.0f}/year**
**Target Revenue: ${target:,.0f}/year**

Implementation Priority:
1. Low difficulty, high impact: {opportunities[0]['name']}
2. Quick wins: Focus on 1-3 month opportunities
3. Long-term growth: Plan {opportunities[2]['name']} for Q3-Q4
"""
        
        return Response(message=message, break_loop=False)
    
    async def _analyze_life_balance(self, business_name: str, output_dir: str, data: dict):
        """Analyze work-life balance"""
        
        work_hours = data.get('work_hours_week', 50)
        ideal_hours = data.get('ideal_hours_week', 40)
        stress_level = data.get('stress_level', 6)
        exercise_hours = data.get('exercise_hours_week', 3)
        sleep_hours = data.get('sleep_hours_night', 7)
        family_time = data.get('family_time_hours_week', 15)
        life_satisfaction = data.get('life_satisfaction', 7)
        
        # Calculate balance score
        balance_score = self._calculate_balance_score(
            work_hours, ideal_hours, stress_level, 
            exercise_hours, sleep_hours, life_satisfaction
        )
        
        diagram = f"""```mermaid
graph TB
    subgraph "Work ({work_hours}h/week)"
        W1[Stress: {stress_level}/10]
        W2[Ideal: {ideal_hours}h]
    end
    subgraph "Health"
        H1[Exercise: {exercise_hours}h/week]
        H2[Sleep: {sleep_hours}h/night]
    end
    subgraph "Life"
        L1[Family Time: {family_time}h/week]
        L2[Satisfaction: {life_satisfaction}/10]
    end
    
    W1 --> Score[Balance Score: {balance_score}/100]
    H1 --> Score
    L2 --> Score
    
    style Score fill:#e1f5ff
```"""
        
        diagram_file = Path(output_dir) / "life_balance.mmd"
        with open(diagram_file, 'w') as f:
            f.write(diagram)
        
        recommendations = self._get_balance_recommendations(
            work_hours, ideal_hours, stress_level, exercise_hours, sleep_hours
        )
        
        message = f"""
**Work-Life Balance Analysis: {business_name}**

{diagram}

**Balance Score: {balance_score}/100**

Current State:
- Work: {work_hours}h/week (ideal: {ideal_hours}h)
- Stress: {stress_level}/10
- Exercise: {exercise_hours}h/week
- Sleep: {sleep_hours}h/night
- Life Satisfaction: {life_satisfaction}/10

Recommendations:
{recommendations}
"""
        
        return Response(message=message, break_loop=False)
    
    # Helper methods
    
    def _calculate_health_score(self, revenue: float, growth: float, margin: float, ltv_cac: float) -> int:
        """Calculate business health score"""
        score = 0
        
        if growth > 10:
            score += 30
        elif growth > 5:
            score += 20
        elif growth > 0:
            score += 10
        
        if margin > 30:
            score += 25
        elif margin > 20:
            score += 20
        elif margin > 10:
            score += 15
        
        if ltv_cac > 3:
            score += 25
        elif ltv_cac > 2:
            score += 20
        elif ltv_cac > 1:
            score += 10
        
        return min(score, 100)
    
    def _calculate_balance_score(self, work_hours: float, ideal_hours: float, stress: int, 
                                 exercise: float, sleep: float, satisfaction: int) -> int:
        """Calculate work-life balance score"""
        score = 0
        
        work_diff = abs(work_hours - ideal_hours)
        if work_diff < 5:
            score += 25
        elif work_diff < 10:
            score += 15
        
        if stress <= 3:
            score += 25
        elif stress <= 5:
            score += 15
        elif stress <= 7:
            score += 5
        
        if exercise >= 3:
            score += 15
        if sleep >= 7:
            score += 15
        
        if satisfaction >= 8:
            score += 20
        elif satisfaction >= 6:
            score += 10
        
        return min(score, 100)
    
    def _get_health_recommendations(self, score: int, growth: float, margin: float, ltv_cac: float) -> str:
        """Generate health recommendations"""
        recs = []
        
        if score < 50:
            recs.append("⚠️ Critical: Business health needs immediate attention")
        
        if growth < 5:
            recs.append("📈 Focus on growth initiatives - aim for 10%+ monthly growth")
        
        if margin < 20:
            recs.append("💰 Improve profit margins through pricing or cost optimization")
        
        if ltv_cac < 3:
            recs.append("🎯 Improve customer economics - target 3:1 LTV/CAC ratio")
        
        if not recs:
            recs.append("✅ Business health is strong - focus on scaling")
        
        return "\n".join(f"- {r}" for r in recs)
    
    def _get_time_recommendations(self, efficiency: float, deep_work: float, meetings: float) -> str:
        """Generate time recommendations"""
        recs = []
        
        if efficiency < 40:
            recs.append("⏰ Critical: Increase deep work time to 40%+ of total work hours")
        
        if deep_work < 15:
            recs.append("🎯 Schedule more focused work blocks - target 20+ hours/week")
        
        if meetings > 15:
            recs.append("📅 Reduce meeting time - decline unnecessary meetings")
        
        if not recs:
            recs.append("✅ Time allocation is optimal")
        
        return "\n".join(f"- {r}" for r in recs)
    
    def _get_balance_recommendations(self, work: float, ideal: float, stress: int, 
                                    exercise: float, sleep: float) -> str:
        """Generate balance recommendations"""
        recs = []
        
        if work > ideal + 10:
            recs.append("⚠️ Working significantly over ideal hours - delegate or automate")
        
        if stress > 7:
            recs.append("🧘 High stress level - implement daily stress management practices")
        
        if exercise < 3:
            recs.append("🏃 Increase exercise to 3+ hours per week")
        
        if sleep < 7:
            recs.append("😴 Prioritize 7-8 hours of sleep per night")
        
        if not recs:
            recs.append("✅ Work-life balance is healthy")
        
        return "\n".join(f"- {r}" for r in recs)
    
    def _collect_reports(self, output_dir: str) -> dict:
        """Collect generated reports"""
        reports = {}
        
        summary_file = Path(output_dir) / "executive_summary.md"
        if summary_file.exists():
            with open(summary_file, 'r') as f:
                reports['executive_summary'] = f.read()
        
        return reports
