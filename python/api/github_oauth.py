from python.helpers.api import ApiHandler
from python.helpers.github_auth import GITHUB_CLIENT_ID, create_flow
from flask import Request
import httpx


class GithubOauth(ApiHandler):
    """Initiate GitHub Device Flow OAuth.

    POSTs to GitHub's device/code endpoint and returns the user_code
    and verification_uri for the user to complete authorization.
    """

    async def process(self, input: dict, request: Request) -> dict:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://github.com/login/device/code",
                    data={
                        "client_id": GITHUB_CLIENT_ID,
                        "scope": "repo,user",
                    },
                    headers={"Accept": "application/json"},
                )

                if response.status_code != 200:
                    return {
                        "success": False,
                        "error": "Failed to start device flow. Ensure Device Flow is enabled in the GitHub OAuth App settings.",
                    }

                data = response.json()

                if "error" in data:
                    return {
                        "success": False,
                        "error": data.get("error_description", data["error"]),
                    }

                device_code = data.get("device_code", "")
                user_code = data.get("user_code", "")
                verification_uri = data.get("verification_uri", "")
                expires_in = data.get("expires_in", 900)
                interval = data.get("interval", 5)

                if not device_code or not user_code:
                    return {"success": False, "error": "Invalid response from GitHub"}

                flow_id = create_flow(device_code, expires_in, interval)

                return {
                    "success": True,
                    "flow_id": flow_id,
                    "user_code": user_code,
                    "verification_uri": verification_uri,
                    "interval": interval,
                }

        except Exception as e:
            return {"success": False, "error": f"Failed to start GitHub device flow: {str(e)[:200]}"}
