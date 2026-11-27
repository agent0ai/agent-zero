from helpers.socket_api import SocketHandler


class Ping(SocketHandler):
    async def process(self, input: dict) -> dict:
        return {"message": "pong"}
