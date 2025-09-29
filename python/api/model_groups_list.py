from python.helpers.api import ApiHandler, Request, Response
from python.helpers import model_groups


class ModelGroupsList(ApiHandler):
    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        data = model_groups.get_all()
        return data

