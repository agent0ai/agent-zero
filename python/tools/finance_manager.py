"""
Finance Manager Tool for Agent Jumbo
Mock-friendly finance automation with ingest, categorize, and reporting actions.
"""

import json

from python.helpers import files
from python.helpers.life_events import emit_event
from python.helpers.notification import AgentNotification
from python.helpers.tool import Response, Tool


class FinanceManagerTool(Tool):
    def __init__(self, agent, name: str, method: str | None, args: dict, message: str, loop_data=None, **kwargs):
        super().__init__(agent, name, method, args, message, loop_data, **kwargs)
        from instruments.custom.finance_manager.finance_manager import FinanceManager

        db_path = files.get_abs_path("./instruments/custom/finance_manager/data/finance_manager.db")
        self.manager = FinanceManager(db_path)

    async def execute(self, **kwargs):
        action = (self.args.get("action") or "").lower()

        if action == "connect_account":
            provider = self.args.get("provider", "mock")
            mock = bool(self.args.get("mock", True))
            result = self.manager.connect_account(provider=provider, mock=mock)
            emit_event("finance.account_connected", {"account_id": result.get("id"), "provider": provider})
            return Response(message=json.dumps(result, indent=4), break_loop=False)

        if action == "sync_transactions":
            account_id = int(self.args.get("account_id"))
            start = self.args.get("start")
            end = self.args.get("end")
            result = self.manager.sync_transactions(account_id, start, end)
            emit_event("finance.txn_ingested", {"account_id": account_id, "start": start, "end": end})
            return Response(message=json.dumps(result, indent=4), break_loop=False)

        if action == "get_auth_url":
            provider = self.args.get("provider", "plaid")
            result = {"auth_url": self.manager.get_auth_url(provider)}
            return Response(message=json.dumps(result, indent=4), break_loop=False)

        if action == "categorize":
            txn_id = int(self.args.get("transaction_id"))
            category = self.args.get("category")
            self.manager.categorize(txn_id, category)
            emit_event("finance.txn_categorized", {"transaction_id": txn_id, "category": category})
            return Response(message=json.dumps({"updated": True}, indent=4), break_loop=False)

        if action == "upload_receipt":
            txn_id = int(self.args.get("transaction_id"))
            file_path = self.args.get("file_path")
            result = self.manager.upload_receipt(txn_id, file_path)
            emit_event("finance.receipt_uploaded", {"transaction_id": txn_id, "file_path": file_path})
            return Response(message=json.dumps(result, indent=4), break_loop=False)

        if action == "generate_report":
            period = self.args.get("period")
            account_id = self.args.get("account_id")
            result = self.manager.generate_report(period, account_id=account_id)
            emit_event("finance.report_generated", {"period": period, "account_id": account_id})
            if result.get("total_amount", 0) < 0:
                AgentNotification.warning("Expenses exceed income for the period", "Finance")
            return Response(message=json.dumps(result, indent=4), break_loop=False)

        if action == "estimate_tax":
            period = self.args.get("period")
            account_id = self.args.get("account_id")
            result = self.manager.estimate_tax(period, account_id=account_id)
            emit_event("finance.tax_estimated", {"period": period, "account_id": account_id})
            AgentNotification.info("Tax estimate generated", "Finance")
            return Response(message=json.dumps(result, indent=4), break_loop=False)

        if action == "roi_snapshot":
            period = self.args.get("period")
            account_id = self.args.get("account_id")
            result = self.manager.roi_snapshot(period, account_id=account_id)
            emit_event("finance.roi_snapshot", {"period": period, "account_id": account_id})
            return Response(message=json.dumps(result, indent=4), break_loop=False)

        if action == "export_business_xray":
            period = self.args.get("period")
            account_id = self.args.get("account_id")
            result = self.manager.export_business_xray_data(period, account_id=account_id)
            emit_event("finance.business_xray_export", {"period": period, "account_id": account_id})
            return Response(message=json.dumps(result, indent=4), break_loop=False)

        if action == "link_property_expense":
            txn_id = int(self.args.get("transaction_id"))
            property_id = int(self.args.get("property_id"))
            result = self.manager.link_property_expense(txn_id, property_id)
            emit_event("finance.property_linked", {"transaction_id": txn_id, "property_id": property_id})
            return Response(message=json.dumps(result, indent=4), break_loop=False)

        return Response(
            message="Unknown action. Use connect_account, sync_transactions, categorize, upload_receipt, generate_report, estimate_tax, roi_snapshot, export_business_xray, link_property_expense.",
            break_loop=False,
        )
