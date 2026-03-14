"""Test Mahoosuc OS native tool conversion"""

import pytest

from python.helpers.tool import Response


class TestNativeToolConversion:
    """Test native Agent Jumbo tools converted from Mahoosuc commands"""

    @pytest.mark.asyncio
    async def test_finance_report_tool_exists(self):
        """Should have FinanceReport tool converted from /finance:report"""
        from python.tools.mahoosuc_finance_report import FinanceReport

        assert FinanceReport is not None
        assert hasattr(FinanceReport, "execute")

    @pytest.mark.asyncio
    async def test_finance_report_execution(self):
        """Should generate finance report"""
        from python.tools.mahoosuc_finance_report import FinanceReport

        tool = FinanceReport(
            agent=None,
            name="mahoosuc_finance_report",
            method="",
            args={"type": "income", "period": "month"},
            message="",
            loop_data=None,
        )

        response = await tool.execute()

        assert isinstance(response, Response)
        assert response.message is not None
        assert "income" in response.message.lower() or "report" in response.message.lower()
        assert response.break_loop is False

    @pytest.mark.asyncio
    async def test_finance_report_default_parameters(self):
        """Should use default parameters when not specified"""
        from python.tools.mahoosuc_finance_report import FinanceReport

        tool = FinanceReport(agent=None, name="mahoosuc_finance_report", method="", args={}, message="", loop_data=None)

        response = await tool.execute()

        assert isinstance(response, Response)
        assert response.message is not None
