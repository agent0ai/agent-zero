"""
Extended Email Tool for Agent Jumbo - Phase 2/3
Adds Gmail API OAuth2 and Push Notifications support
"""

import os

from python.helpers import settings
from python.helpers.tool import Response, Tool


class EmailAdvanced(Tool):
    """
    Advanced email operations using Gmail API.
    Supports OAuth2 authentication, labels, drafts, and push notifications.
    """

    async def execute(self, **kwargs):
        """Execute advanced email action"""

        action = self.args.get("action", "").lower()

        # Gmail API actions
        if action == "authenticate":
            return await self._authenticate_account()
        elif action == "send_gmail":
            return await self._send_via_gmail_api()
        elif action == "read_gmail":
            return await self._read_via_gmail_api()
        elif action == "search_advanced":
            return await self._advanced_search()
        elif action == "create_label":
            return await self._create_label()
        elif action == "list_labels":
            return await self._list_labels()
        elif action == "apply_labels":
            return await self._apply_labels()
        elif action == "create_draft":
            return await self._create_draft()
        elif action == "list_drafts":
            return await self._list_drafts()
        elif action == "send_draft":
            return await self._send_draft()
        elif action == "list_accounts":
            return await self._list_accounts()
        elif action == "enable_push":
            return await self._enable_push_notifications()
        elif action == "disable_push":
            return await self._disable_push_notifications()
        else:
            return Response(
                message=f"Unknown action: {action}. See documentation for available Gmail API actions.",
                break_loop=False,
            )

    def _resolve_account_name(self, requested_name: str | None):
        if requested_name:
            requested_name = requested_name.strip()
        current_settings = settings.get_settings()
        gmail_accounts = current_settings.get("gmail_accounts", {})

        if requested_name and (requested_name != "default" or requested_name in gmail_accounts):
            return requested_name, None

        if not gmail_accounts:
            return None, Response(
                message="❌ No Gmail accounts configured. Add one in Settings → External → Gmail Accounts.",
                break_loop=False,
            )

        if len(gmail_accounts) == 1:
            return next(iter(gmail_accounts.keys())), None

        account_list = ", ".join(sorted(gmail_accounts.keys()))
        return None, Response(
            message=(
                "❌ Multiple Gmail accounts configured. Please specify `account_name`.\n\n"
                f"**Available:** {account_list}"
            ),
            break_loop=False,
        )

    async def _authenticate_account(self):
        """Authenticate Gmail account via OAuth2"""
        try:
            from python.helpers.gmail_oauth2 import GmailOAuth2Handler

            account_name = self.args.get("account_name", "default")
            credentials_json = self.args.get("credentials_json_path")

            handler = GmailOAuth2Handler()
            result = handler.authenticate_account(account_name, credentials_json)

            if result.get("success"):
                message = f"✅ Successfully authenticated account: {account_name}\n\n"
                message += f"**Email:** {result.get('email', 'Unknown')}\n"
                message += f"**Scopes:** {len(result.get('scopes', []))} permissions granted\n"
            else:
                message = "❌ Authentication failed\n\n"
                message += f"**Error:** {result.get('error')}\n"
                if result.get("help"):
                    message += f"**Help:** {result.get('help')}\n"
                if result.get("install_command"):
                    message += f"\n**Install:** `{result.get('install_command')}`\n"

            return Response(message=message, break_loop=False)

        except ImportError:
            return Response(
                message="❌ Gmail API libraries not installed\n\nRun: `pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client`",
                break_loop=False,
            )
        except Exception as e:
            return Response(message=f"❌ Authentication error: {e!s}", break_loop=False)

    async def _send_via_gmail_api(self):
        """Send email via Gmail API"""
        try:
            from python.helpers.gmail_api_client import GmailAPIClient

            account_name, error_response = self._resolve_account_name(self.args.get("account_name"))
            if error_response:
                return error_response
            client = GmailAPIClient(account_name)

            to = self.args.get("to", [])
            if isinstance(to, str):
                to = [to]

            result = client.send_email(
                to=to,
                subject=self.args.get("subject", ""),
                body=self.args.get("body", ""),
                cc=self.args.get("cc"),
                bcc=self.args.get("bcc"),
                attachments=self.args.get("attachments"),
                html=self.args.get("html", False),
                from_name=self.args.get("from_name"),
                labels=self.args.get("labels"),
                thread_id=self.args.get("thread_id"),
            )

            if result.get("success"):
                message = "✅ Email sent via Gmail API\n\n"
                message += f"**Account:** {account_name}\n"
                message += f"**To:** {', '.join(result['to'])}\n"
                message += f"**Subject:** {result['subject']}\n"
                message += f"**Message ID:** {result['message_id']}\n"
                if result.get("thread_id"):
                    message += f"**Thread ID:** {result['thread_id']}\n"
                if result.get("labels"):
                    message += f"**Labels:** {', '.join(result['labels'])}\n"
            else:
                message = "❌ Failed to send email\n\n"
                message += f"**Error:** {result.get('error')}\n"

            return Response(message=message, break_loop=False)

        except Exception as e:
            return Response(message=f"❌ Gmail API send error: {e!s}", break_loop=False)

    async def _read_via_gmail_api(self):
        """Read emails via Gmail API"""
        try:
            from python.helpers.gmail_api_client import GmailAPIClient

            account_name, error_response = self._resolve_account_name(self.args.get("account_name"))
            if error_response:
                return error_response
            client = GmailAPIClient(account_name)

            emails = client.read_emails(
                query=self.args.get("query"),
                max_results=self.args.get("max_results", 10),
                label_ids=self.args.get("label_ids"),
                include_spam_trash=self.args.get("include_spam_trash", False),
            )

            if not emails:
                return Response(message="No emails found matching criteria.", break_loop=False)

            message = f"📧 Found {len(emails)} email(s) via Gmail API:\n\n"

            for i, email in enumerate(emails, 1):
                message += f"**{i}. From:** {email.get('from', 'Unknown')}\n"
                message += f"   **Subject:** {email.get('subject', 'No subject')}\n"
                message += f"   **Date:** {email.get('date', 'Unknown')}\n"
                message += f"   **Labels:** {', '.join(email.get('labels', []))}\n"
                message += f"   **Unread:** {'Yes' if email.get('is_unread') else 'No'}\n"

                snippet = email.get("snippet", "")[:150]
                if len(email.get("snippet", "")) > 150:
                    snippet += "..."
                message += f"   **Preview:** {snippet}\n\n"

            return Response(message=message, break_loop=False)

        except Exception as e:
            return Response(message=f"❌ Gmail API read error: {e!s}", break_loop=False)

    async def _advanced_search(self):
        """Advanced email search with multiple criteria"""
        try:
            from python.helpers.gmail_api_client import GmailAPIClient

            account_name, error_response = self._resolve_account_name(self.args.get("account_name"))
            if error_response:
                return error_response
            client = GmailAPIClient(account_name)

            emails = client.search_emails(
                sender=self.args.get("sender"),
                recipient=self.args.get("recipient"),
                subject=self.args.get("subject"),
                keywords=self.args.get("keywords"),
                has_attachment=self.args.get("has_attachment"),
                is_unread=self.args.get("is_unread"),
                after_date=self.args.get("after_date"),
                before_date=self.args.get("before_date"),
                max_results=self.args.get("max_results", 10),
            )

            if not emails:
                return Response(message="No emails found matching search criteria.", break_loop=False)

            message = f"🔍 Search Results: {len(emails)} email(s)\n\n"

            for i, email in enumerate(emails, 1):
                message += f"**{i}.** {email.get('from')} → {email.get('subject')}\n"
                message += f"     Date: {email.get('date')} | Unread: {email.get('is_unread')}\n\n"

            return Response(message=message, break_loop=False)

        except Exception as e:
            return Response(message=f"❌ Search error: {e!s}", break_loop=False)

    async def _create_label(self):
        """Create Gmail label"""
        try:
            from python.helpers.gmail_api_client import GmailAPIClient

            account_name, error_response = self._resolve_account_name(self.args.get("account_name"))
            if error_response:
                return error_response
            client = GmailAPIClient(account_name)

            label_name = self.args.get("label_name")
            if not label_name:
                return Response(message="❌ Missing required parameter: label_name", break_loop=False)

            result = client.create_label(
                name=label_name,
                label_list_visibility=self.args.get("label_list_visibility", "labelShow"),
                message_list_visibility=self.args.get("message_list_visibility", "show"),
            )

            if result.get("success"):
                message = "✅ Label created successfully\n\n"
                message += f"**Name:** {result['label_name']}\n"
                message += f"**ID:** {result['label_id']}\n"
            else:
                message = f"❌ Failed to create label\n\n**Error:** {result.get('error')}\n"

            return Response(message=message, break_loop=False)

        except Exception as e:
            return Response(message=f"❌ Label creation error: {e!s}", break_loop=False)

    async def _list_labels(self):
        """List all Gmail labels"""
        try:
            from python.helpers.gmail_api_client import GmailAPIClient

            account_name, error_response = self._resolve_account_name(self.args.get("account_name"))
            if error_response:
                return error_response
            client = GmailAPIClient(account_name)

            labels = client.list_labels()

            if not labels:
                return Response(message="No labels found.", break_loop=False)

            message = f"🏷️ Gmail Labels ({len(labels)} total):\n\n"

            # Group by type
            system_labels = [l for l in labels if l["type"] == "system"]
            user_labels = [l for l in labels if l["type"] == "user"]

            if system_labels:
                message += "**System Labels:**\n"
                for label in system_labels:
                    message += f"  - {label['label_name']} (ID: {label['label_id']})\n"
                message += "\n"

            if user_labels:
                message += "**User Labels:**\n"
                for label in user_labels:
                    message += f"  - {label['label_name']} (ID: {label['label_id']})\n"

            return Response(message=message, break_loop=False)

        except Exception as e:
            return Response(message=f"❌ Label list error: {e!s}", break_loop=False)

    async def _apply_labels(self):
        """Apply labels to messages"""
        try:
            from python.helpers.gmail_api_client import GmailAPIClient

            account_name, error_response = self._resolve_account_name(self.args.get("account_name"))
            if error_response:
                return error_response
            client = GmailAPIClient(account_name)

            message_ids = self.args.get("message_ids", [])
            label_ids = self.args.get("label_ids", [])

            if not message_ids or not label_ids:
                return Response(message="❌ Missing required parameters: message_ids and label_ids", break_loop=False)

            result = client.apply_labels(message_ids, label_ids)

            if result.get("success"):
                message = "✅ Labels applied successfully\n\n"
                message += f"**Messages modified:** {result['messages_modified']}\n"
                message += f"**Labels applied:** {', '.join(result['labels_applied'])}\n"
            else:
                message = f"❌ Failed to apply labels\n\n**Error:** {result.get('error')}\n"

            return Response(message=message, break_loop=False)

        except Exception as e:
            return Response(message=f"❌ Apply labels error: {e!s}", break_loop=False)

    async def _create_draft(self):
        """Create email draft"""
        try:
            from python.helpers.gmail_api_client import GmailAPIClient

            account_name, error_response = self._resolve_account_name(self.args.get("account_name"))
            if error_response:
                return error_response
            client = GmailAPIClient(account_name)

            to = self.args.get("to", [])
            if isinstance(to, str):
                to = [to]

            result = client.create_draft(
                to=to,
                subject=self.args.get("subject", ""),
                body=self.args.get("body", ""),
                cc=self.args.get("cc"),
                bcc=self.args.get("bcc"),
                attachments=self.args.get("attachments"),
                html=self.args.get("html", False),
            )

            if result.get("success"):
                message = "✅ Draft created successfully\n\n"
                message += f"**Draft ID:** {result['draft_id']}\n"
                message += f"**Message ID:** {result['message_id']}\n"
            else:
                message = f"❌ Failed to create draft\n\n**Error:** {result.get('error')}\n"

            return Response(message=message, break_loop=False)

        except Exception as e:
            return Response(message=f"❌ Draft creation error: {e!s}", break_loop=False)

    async def _list_drafts(self):
        """List email drafts"""
        try:
            from python.helpers.gmail_api_client import GmailAPIClient

            account_name, error_response = self._resolve_account_name(self.args.get("account_name"))
            if error_response:
                return error_response
            client = GmailAPIClient(account_name)

            drafts = client.list_drafts(max_results=self.args.get("max_results", 10))

            if not drafts:
                return Response(message="No drafts found.", break_loop=False)

            message = f"📝 Found {len(drafts)} draft(s):\n\n"

            for i, draft in enumerate(drafts, 1):
                message += f"**{i}.** Draft ID: {draft['draft_id']}\n"
                message += f"     Message ID: {draft['message_id']}\n\n"

            return Response(message=message, break_loop=False)

        except Exception as e:
            return Response(message=f"❌ List drafts error: {e!s}", break_loop=False)

    async def _send_draft(self):
        """Send existing draft"""
        try:
            from python.helpers.gmail_api_client import GmailAPIClient

            account_name, error_response = self._resolve_account_name(self.args.get("account_name"))
            if error_response:
                return error_response
            client = GmailAPIClient(account_name)

            draft_id = self.args.get("draft_id")
            if not draft_id:
                return Response(message="❌ Missing required parameter: draft_id", break_loop=False)

            result = client.send_draft(draft_id)

            if result.get("success"):
                message = "✅ Draft sent successfully\n\n"
                message += f"**Message ID:** {result['message_id']}\n"
                message += f"**Thread ID:** {result.get('thread_id')}\n"
            else:
                message = f"❌ Failed to send draft\n\n**Error:** {result.get('error')}\n"

            return Response(message=message, break_loop=False)

        except Exception as e:
            return Response(message=f"❌ Send draft error: {e!s}", break_loop=False)

    async def _list_accounts(self):
        """List all authenticated Gmail accounts"""
        try:
            from python.helpers.gmail_oauth2 import GmailOAuth2Handler

            handler = GmailOAuth2Handler()
            accounts = handler.list_accounts()

            if not accounts:
                return Response(
                    message="No authenticated accounts found.\n\nUse `authenticate` action to add an account.",
                    break_loop=False,
                )

            message = f"📧 Authenticated Gmail Accounts ({len(accounts)}):\n\n"

            for account in accounts:
                message += f"**Account:** {account['account_name']}\n"
                message += f"**Email:** {account.get('email', 'Unknown')}\n"
                message += (
                    f"**Status:** {'✅ Authenticated' if account['authenticated'] else '❌ Not authenticated'}\n\n"
                )

            return Response(message=message, break_loop=False)

        except Exception as e:
            return Response(message=f"❌ List accounts error: {e!s}", break_loop=False)

    async def _enable_push_notifications(self):
        """Enable Gmail push notifications"""
        try:
            from python.helpers.gmail_push_notifications import GmailPushNotifications

            account_name, error_response = self._resolve_account_name(self.args.get("account_name"))
            if error_response:
                return error_response
            project_id = self.args.get("project_id") or os.getenv("GOOGLE_CLOUD_PROJECT_ID")

            if not project_id:
                return Response(
                    message="❌ Missing Google Cloud project ID\n\nSet GOOGLE_CLOUD_PROJECT_ID environment variable.",
                    break_loop=False,
                )

            push = GmailPushNotifications(project_id=project_id)

            # Setup topic/subscription
            setup_result = push.setup_topic_and_subscription()
            if not setup_result.get("success"):
                return Response(message=f"❌ Failed to setup Pub/Sub\n\n{setup_result.get('error')}", break_loop=False)

            # Enable push
            result = push.enable_push_notifications(account_name)

            if result.get("success"):
                message = "✅ Push notifications enabled\n\n"
                message += f"**Account:** {account_name}\n"
                message += f"**Topic:** {result.get('topic')}\n"
                message += f"**History ID:** {result.get('history_id')}\n"
                message += f"**Expiration:** {result.get('expiration')}\n"
            else:
                message = f"❌ Failed to enable push notifications\n\n{result.get('error')}"

            return Response(message=message, break_loop=False)

        except ImportError:
            return Response(
                message="❌ Google Cloud Pub/Sub library not installed\n\nRun: `pip install google-cloud-pubsub`",
                break_loop=False,
            )
        except Exception as e:
            return Response(message=f"❌ Push notification error: {e!s}", break_loop=False)

    async def _disable_push_notifications(self):
        """Disable Gmail push notifications"""
        try:
            from python.helpers.gmail_push_notifications import GmailPushNotifications

            account_name, error_response = self._resolve_account_name(self.args.get("account_name"))
            if error_response:
                return error_response
            project_id = self.args.get("project_id") or os.getenv("GOOGLE_CLOUD_PROJECT_ID")

            push = GmailPushNotifications(project_id=project_id)
            result = push.disable_push_notifications(account_name)

            if result.get("success"):
                message = f"✅ Push notifications disabled\n\n**Account:** {account_name}"
            else:
                message = f"❌ Failed to disable push notifications\n\n{result.get('error')}"

            return Response(message=message, break_loop=False)

        except Exception as e:
            return Response(message=f"❌ Disable push error: {e!s}", break_loop=False)
