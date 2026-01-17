### finance_manager

Finance automation tool for ingesting transactions, categorizing expenses, and generating reports.

Actions:
- `connect_account(provider, mock=true)`
- `get_auth_url(provider)`
- `sync_transactions(account_id, start, end)`
- `categorize(transaction_id, category)`
- `upload_receipt(transaction_id, file_path)`
- `generate_report(period, account_id=null)`
- `estimate_tax(period, account_id=null)`
- `roi_snapshot(period, account_id=null)`
- `export_business_xray(period, account_id=null)`
- `link_property_expense(transaction_id, property_id)`

Examples:
```
{{finance_manager(action="connect_account", provider="mock", mock=true)}}
{{finance_manager(action="sync_transactions", account_id=1, start="2025-01-01", end="2025-01-31")}}
{{finance_manager(action="generate_report", period="2025-01")}}
```
