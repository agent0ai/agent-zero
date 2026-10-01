from helpers.extension import Extension
from plugins._context_window.helpers.usage import capture_provider_usage


class RecordProviderUsage(Extension):
    def execute(self, data: dict | None = None, **kwargs):
        payload = data if isinstance(data, dict) else {}
        if not payload.get("exception"):
            capture_provider_usage(self.agent, payload.get("result"))
