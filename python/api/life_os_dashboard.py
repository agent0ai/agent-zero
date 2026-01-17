"""
Life OS Dashboard API
Aggregates data for the Life OS dashboard UI.
"""

from python.helpers import files
from python.helpers.api import ApiHandler


class LifeOsDashboard(ApiHandler):
    async def process(self, input: dict, request) -> dict:
        try:
            from instruments.custom.life_os.life_manager import LifeOSManager

            db_path = files.get_abs_path("./instruments/custom/life_os/data/life_os.db")
            manager = LifeOSManager(db_path)

            dashboard = manager.get_dashboard()

            return {"success": True, "dashboard": dashboard}
        except Exception as e:
            return {"success": False, "error": str(e)}
