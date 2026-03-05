from channels.generic.websocket import AsyncJsonWebsocketConsumer


class LobbyConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("lobby", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("lobby", self.channel_name)

    async def lobby_message(self, event):
        await self.send_json(
            {
                "event": event["event"],
                "payload": event["payload"],
            }
        )
