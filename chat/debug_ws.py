from channels.generic.websocket import AsyncWebsocketConsumer

class DebugWS(AsyncWebsocketConsumer):
    async def connect(self):
        print(f"[WS DEBUG] CONNECT path={self.scope.get('path')} qs={self.scope.get('query_string')}")
        await self.accept()
        await self.send_text("hello from debug")
    async def receive(self, text_data=None, bytes_data=None):
        print(f"[WS DEBUG] RECV text={text_data}")
        if text_data:
            await self.send_text(f"echo: {text_data}")
    async def disconnect(self, code):
        print(f"[WS DEBUG] DISCONNECT code={code}")