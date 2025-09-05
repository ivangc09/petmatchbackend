import os
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from .models import Message, make_room


class DMConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        if not user or user.is_anonymous:
            await self.close()
            return

        try:
            self.peer_id = int(self.scope['url_route']['kwargs']['peer_id'])
        except Exception:
            await self.close()
            return

        # Sala compartida (IDs ordenados)
        self.room_name = make_room(user.id, self.peer_id)

        # Logs
        print(f"[WS CONNECT] pid={os.getpid()} user={user.id} peer={self.peer_id} room={self.room_name}")

        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, "room_name"):
            await self.channel_layer.group_discard(self.room_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        # Esperamos { type: "message", text: "...", client_id?: "..." }
        if content.get("type") != "message":
            return

        text = (content.get("text") or "").strip()
        if not text:
            return

        client_id = content.get("client_id")  # puede venir None y no pasa nada

        # Persistir en DB
        sender = self.scope["user"]
        try:
            User = get_user_model()
            recipient = await sync_to_async(User.objects.get)(id=self.peer_id)
        except User.DoesNotExist:
            # Si el peer no existe, no persistimos ni broadcast
            return

        msg = await sync_to_async(Message.objects.create)(
            sender=sender,
            receiver=recipient,
            content=text,
            room_name=self.room_name,
        )

        # Log envío
        print(f"[WS MSG] pid={os.getpid()} room={self.room_name} sender={sender.id} -> msg_id={msg.id} client_id={client_id}")

        # Broadcast a TODOS en la sala (emisor + receptor)
        await self.channel_layer.group_send(
            self.room_name,
            {
                "type": "chat.message",
                "message": {
                    "id": msg.id,
                    "sender_id": msg.sender_id,
                    "text": msg.content,
                    "created_at": msg.timestamp.isoformat(),
                    "client_id": client_id,
                },
            },
        )

    async def chat_message(self, event):
        await self.send_json(event["message"])  