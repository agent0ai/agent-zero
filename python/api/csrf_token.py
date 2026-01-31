import secrets
from urllib.parse import urlparse

from python.helpers.api import (
    ApiHandler,
    Input,
    Output,
    Request,
    Response,
    session,
)
from python.helpers import runtime, dotenv, login
import fnmatch


class GetCsrfToken(ApiHandler):

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET"]

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    async def process(self, input: Input, request: Request) -> Output:
        # check for allowed origin to prevent dns rebinding attacks
        origin_check = await self.check_allowed_origin(request)
        if not origin_check["ok"]:
            origin = self.get_origin_from_request(request)
            allowed = origin_check.get("allowed_origins", "")

            return {
                "ok": False,
                "error": (
                    f"Origin '{origin}' not allowed when login is disabled. "
                    f"Set login and password or add your URL to ALLOWED_ORIGINS env variable. "
                    f"Currently allowed origins: {allowed}"
                ),
            }

        # generate a csrf token if it doesn't exist
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_urlsafe(32)

        # return the csrf token and runtime id
        return {
            "ok": True,
            "token": session["csrf_token"],
            "runtime_id": runtime.get_runtime_id(),
        }

    async def check_allowed_origin(self, request: Request):
        # if login is required, allow all origins
        if login.is_login_required():
            return {"ok": True, "origin": "", "allowed_origins": ""}

        return await self.is_allowed_origin(request)

    async def is_allowed_origin(self, request: Request):
        origin = self.get_origin_from_request(request)

        allowed_origins = dotenv.get("ALLOWED_ORIGINS", "")
        allowed_list = [o.strip() for o in allowed_origins.split(",") if o.strip()]

        if not allowed_list:
            return {"ok": False, "origin": origin, "allowed_origins": allowed_origins}

        for pattern in allowed_list:
            if fnmatch.fnmatch(origin, pattern):
                return {"ok": True, "origin": origin, "allowed_origins": allowed_origins}

        return {"ok": False, "origin": origin, "allowed_origins": allowed_origins}

    def get_origin_from_request(self, request: Request) -> str:
        origin = request.headers.get("origin") or request.headers.get("referer") or ""
        if not origin:
            return ""
        parsed = urlparse(origin)
        return f"{parsed.scheme}://{parsed.netloc}"
