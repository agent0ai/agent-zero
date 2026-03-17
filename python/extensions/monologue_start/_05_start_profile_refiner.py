from python.helpers.extension import Extension
from python.surveys.profile_refiner import ensure_profile_refiner_running


class StartProfileRefiner(Extension):
    async def execute(self, **kwargs):
        ensure_profile_refiner_running(self.agent)

