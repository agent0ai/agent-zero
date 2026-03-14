import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "instruments" / "custom" / "workflow_engine" / "data" / "workflow.db"


def populate_templates():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    templates = [
        {
            "name": "Sales Development (SDR) Outreach",
            "version": "1.0.0",
            "description": "Standard B2B prospecting and outreach sequence.",
            "workflow_type": "service_delivery",
            "definition": {
                "id": "sdr_outreach",
                "name": "Sales Development (SDR) Outreach",
                "stages": [
                    {
                        "id": "prospecting",
                        "name": "Lead Prospecting",
                        "type": "research",
                        "tasks": [
                            {"id": "identify_leads", "name": "Identify Target Leads", "required_role": "researcher"},
                            {"id": "filter_icp", "name": "Filter by ICP Criteria"},
                        ],
                    },
                    {
                        "id": "enrichment",
                        "name": "Lead Enrichment",
                        "type": "research",
                        "tasks": [
                            {"id": "find_emails", "name": "Find Verified Emails", "required_role": "developer"},
                            {"id": "linkedin_profile", "name": "Scrape LinkedIn Details"},
                        ],
                    },
                    {
                        "id": "outreach",
                        "name": "Outreach Execution",
                        "type": "communication",
                        "tasks": [
                            {"id": "write_drafts", "name": "Generate Personalized Drafts"},
                            {"id": "send_initial", "name": "Send Initial Touchpoint"},
                            {"id": "schedule_followup", "name": "Schedule Day 3 Follow-up"},
                        ],
                    },
                ],
                "settings": {"require_approvals": True},
            },
        },
        {
            "name": "Employee Onboarding",
            "version": "1.1.0",
            "description": "Automated onboarding process for new hires.",
            "workflow_type": "service_delivery",
            "definition": {
                "id": "employee_onboarding",
                "name": "Employee Onboarding",
                "stages": [
                    {
                        "id": "paperwork",
                        "name": "Documentation & Compliance",
                        "tasks": [
                            {"id": "gather_id", "name": "Collect Identification Documents"},
                            {"id": "sign_contract", "name": "Verify Signed Employment Contract"},
                        ],
                    },
                    {
                        "id": "it_setup",
                        "name": "IT & Account Provisioning",
                        "tasks": [
                            {"id": "create_email", "name": "Create GSuite/Outlook Account"},
                            {"id": "slack_invite", "name": "Invite to Slack/Discord Groups"},
                            {"id": "jira_access", "name": "Grant Jira/GitHub Permissions"},
                        ],
                    },
                    {
                        "id": "orientation",
                        "name": "Initial Orientation",
                        "tasks": [
                            {"id": "welcome_call", "name": "Schedule Welcome Call"},
                            {"id": "handbook_review", "name": "Assign Employee Handbook Reading"},
                        ],
                    },
                ],
            },
        },
        {
            "name": "Content Marketing Lifecycle",
            "version": "1.0.0",
            "description": "End-to-end content creation from SEO research to publishing.",
            "workflow_type": "product_development",
            "definition": {
                "id": "content_marketing",
                "name": "Content Marketing Lifecycle",
                "stages": [
                    {
                        "id": "planning",
                        "name": "Content Planning",
                        "tasks": [
                            {"id": "keyword_research", "name": "Perform SEO Keyword Research"},
                            {"id": "topic_selection", "name": "Approve Content Topic"},
                        ],
                    },
                    {
                        "id": "production",
                        "name": "Creative Production",
                        "tasks": [
                            {"id": "drafting", "name": "Write First Draft"},
                            {"id": "graphic_design", "name": "Create Featured Image and Assets"},
                        ],
                    },
                    {
                        "id": "review",
                        "name": "Editing & Proofing",
                        "tasks": [
                            {"id": "seo_check", "name": "Audit for SEO Best Practices"},
                            {"id": "grammar_check", "name": "Final Grammar and Fact Check"},
                        ],
                    },
                    {
                        "id": "distribution",
                        "name": "Publishing & Social",
                        "tasks": [
                            {"id": "cms_upload", "name": "Upload to WordPress/CMS"},
                            {"id": "social_share", "name": "Schedule Social Media Announcements"},
                        ],
                    },
                ],
            },
        },
        {
            "name": "Financial Month-End Close",
            "version": "1.2.0",
            "description": "Standardized process for closing monthly financial books.",
            "workflow_type": "maintenance",
            "definition": {
                "id": "financial_close",
                "name": "Financial Month-End Close",
                "stages": [
                    {
                        "id": "verification",
                        "name": "Transaction Verification",
                        "tasks": [
                            {"id": "check_ledger", "name": "Scan General Ledger for Anomalies"},
                            {"id": "reconcile_bank", "name": "Perform Bank Reconciliation"},
                        ],
                    },
                    {
                        "id": "expense_audit",
                        "name": "Expense & Payroll Audit",
                        "tasks": [
                            {"id": "review_expenses", "name": "Audit Employee Expense Reports"},
                            {"id": "process_payroll", "name": "Finalize Monthly Payroll Run"},
                        ],
                    },
                    {
                        "id": "reporting",
                        "name": "Financial Reporting",
                        "tasks": [
                            {"id": "gen_pl", "name": "Generate P&L Statement"},
                            {"id": "gen_balance", "name": "Generate Balance Sheet"},
                            {"id": "exec_review", "name": "Schedule Executive Financial Review"},
                        ],
                    },
                ],
            },
        },
    ]

    for t in templates:
        try:
            cursor.execute(
                """
                INSERT INTO workflows (name, version, description, workflow_type, definition, is_template)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (t["name"], t["version"], t["description"], t["workflow_type"], json.dumps(t["definition"]), True),
            )
            print(f"Added template: {t['name']}")
        except sqlite3.IntegrityError:
            print(f"Template already exists: {t['name']}")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    populate_templates()
