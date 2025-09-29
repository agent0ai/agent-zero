from python.helpers.api import ApiHandler, Request, Response
from python.helpers import providers


class ModelProvidersList(ApiHandler):
    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        try:
            chat = providers.get_providers('chat')
            embedding = providers.get_providers('embedding')
            return {'chat': chat, 'embedding': embedding}
        except Exception as e:
            return Response(response=f'{{"error":"{str(e)}"}}', status=500, mimetype='application/json')
