from python.helpers.api import ApiHandler
from python.helpers.print_style import PrintStyle
from python.helpers.github_auth import (
    GITHUB_CLIENT_ID,
    get_github_auth,
    save_github_auth,
    clear_github_auth,
    get_flow,
    remove_flow,
)
from flask import Request
import httpx


class GithubCallback(ApiHandler):
    """Poll GitHub device flow for token exchange.

    Frontend calls this with {flow_id} repeatedly until the user
    authorizes, the flow expires, or the user cancels.
    """

    async def process(self, input: dict, request: Request) -> dict:
        flow_id = input.get("flow_id", "")
        if not flow_id:
            return {"status": "error", "error": "Missing flow_id"}

        flow = get_flow(flow_id)
        if not flow:
            return {"status": "error", "error": "Flow expired or not found"}

        try:
            async with httpx.AsyncClient() as client:
                token_response = await client.post(
                    "https://github.com/login/oauth/access_token",
                    data={
                        "client_id": GITHUB_CLIENT_ID,
                        "device_code": flow["device_code"],
                        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    },
                    headers={"Accept": "application/json"},
                )

                if token_response.status_code != 200:
                    return {"status": "error", "error": "GitHub token endpoint returned an error"}

                data = token_response.json()
                error = data.get("error")

                if error == "authorization_pending":
                    return {"status": "pending"}

                if error == "slow_down":
                    # GitHub wants us to increase the polling interval
                    flow["interval"] = data.get("interval", flow["interval"] + 5)
                    return {"status": "pending", "interval": flow["interval"]}

                if error == "expired_token":
                    remove_flow(flow_id)
                    return {"status": "error", "error": "Device code expired. Please try again."}

                if error == "access_denied":
                    remove_flow(flow_id)
                    return {"status": "error", "error": "Authorization was denied."}

                if error:
                    remove_flow(flow_id)
                    return {"status": "error", "error": data.get("error_description", error)}

                access_token = data.get("access_token")
                if not access_token:
                    remove_flow(flow_id)
                    return {"status": "error", "error": "No access token received"}

                # Fetch user info
                user_response = await client.get(
                    "https://api.github.com/user",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/vnd.github+json",
                    },
                )

                if user_response.status_code != 200:
                    remove_flow(flow_id)
                    return {"status": "error", "error": "Failed to fetch GitHub user info"}

                user_data = user_response.json()

                save_github_auth({
                    "access_token": access_token,
                    "user": {
                        "login": user_data.get("login"),
                        "name": user_data.get("name"),
                        "avatar_url": user_data.get("avatar_url"),
                        "html_url": user_data.get("html_url"),
                    },
                })

                remove_flow(flow_id)
                return {"status": "complete"}

        except Exception as e:
            PrintStyle.error(f"GitHub device flow poll error: {e}")
            return {"status": "error", "error": str(e)[:200]}
