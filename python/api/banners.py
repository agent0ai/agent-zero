from python.helpers.api import ApiHandler, Request, Response
from python.helpers import settings as settings_helper
from typing import Any


class GetBanners(ApiHandler):
    """
    API endpoint to get banners for the Welcome Screen.
    
    Input:
        - banners: List of banners already generated on frontend
        - context: Frontend context (URL, browser, time, selected provider, etc.)
    
    Output:
        - banners: List of additional banner objects from backend
    """

    async def process(self, input: dict, request: Request) -> dict | Response:
        frontend_banners = input.get("banners", [])
        frontend_context = input.get("context", {})
        
        backend_banners = []
        
        current_settings = settings_helper.get_settings()
        
        backend_banners.extend(self._run_backend_checks(frontend_context, frontend_banners, current_settings))
        
        return {"banners": backend_banners}

    def _run_backend_checks(
        self, 
        context: dict, 
        frontend_banners: list, 
        settings: dict
    ) -> list[dict[str, Any]]:
        """
        Run all backend banner checks.
        Add new check methods here to extend the system.
        """
        banners = []
        
        # List of check methods to run
        checks = [
            self._check_example_backend,  # Example check (disabled by default)
        ]
        
        for check in checks:
            try:
                result = check(context, frontend_banners, settings)
                if result:
                    if isinstance(result, list):
                        banners.extend(result)
                    else:
                        banners.append(result)
            except Exception as e:
                print(f"Backend banner check failed: {e}")
        
        return banners

    def _check_example_backend(
        self, 
        context: dict, 
        frontend_banners: list, 
        settings: dict
    ) -> dict | list | None:
        """
        Example backend check - disabled by default.
        Shows the pattern for adding new backend checks.
        
        Returns:
            - dict: Single banner object
            - list: Multiple banner objects
            - None: No banner to show
        """
        # Example: Check if a specific condition is met
        # Uncomment to enable this example banner
        # return {
        #     "id": "backend-example",
        #     "type": "info",
        #     "priority": 10,
        #     "title": "Backend Check Example",
        #     "html": "This is an example banner from the backend.",
        #     "dismissible": True,
        #     "source": "backend"
        # }
        return None

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["POST"]
