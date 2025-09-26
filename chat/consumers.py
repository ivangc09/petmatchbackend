import os
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Message, make_room

User = get_user_model()

class DMConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close(code=4401)
            return

        # peer_id desde la URL: ws/chat/u/<peer_id>/
        try:
            self.peer_id = int(self.scope["url_route"]["kwargs"]["peer_id"])
        except Exception:
            await self.close(code=4400)  # bad request
            return

        # Evita chat contigo mismo
        if self.peer_id == user.id:
            await self.close(code=4403)
            return

        # Room canónica (ordenada por ids)
        self.room = make_room(user.id, self.peer_id)

        # Únete al grupo de la room
        await self.channel_layer.group_add(self.room, self.channel_name)
        await self.accept()

        # (Opcional) notificación de presencia
        await self.send_json({"type": "presence", "payload": {"joined": True, "room": self.room}})

    async def disconnect(self, code):
        if hasattr(self, "room"):
            await self.channel_layer.group_discard(self.room, self.channel_name)

    async def receive_json(self, content, **kwargs):
        """
        Espera algo como: { action: "send", text: "hola" }
        """
        user = self.scope["user"]
        action = (content or {}).get("action")

        if action == "send":
            text = (content.get("text") or "").strip()
            if not text:
                await self.send_json({"type": "error", "payload": {"detail": "text requerido"}})
                return

            # Guarda y retransmite
            msg = await self._create_message(user.id, self.peer_id, text, self.room)

            payload = {
                "id": msg["id"],
                "text": msg["content"],
                "sender_id": msg["sender_id"],
                "receiver_id": msg["receiver_id"],
                "created_at": msg["timestamp"],
                "room": self.room,
            }

            # Broadcast a todos en la room (tú y tu peer)
            await self.channel_layer.group_send(
                self.room,
                {"type": "chat.message", "payload": payload}
            )
        else:
            await self.send_json({"type": "error", "payload": {"detail": "action inválida"}})

    async def chat_message(self, event):
        await self.send_json({"type": "message", "payload": event["payload"]})

    # ---------- DB helpers ----------
    @database_sync_to_async
    def _create_message(self, sender_id: int, receiver_id: int, text: str, room: str):
        sender = User.objects.get(id=sender_id)
        receiver = User.objects.get(id=receiver_id)
        m = Message.objects.create(
            sender=sender,
            receiver=receiver,
            content=text,
            room_name=room,
        )
        return {
            "id": m.id,
            "sender_id": m.sender_id,
            "receiver_id": m.receiver_id,
            "content": m.content,
            "timestamp": m.timestamp.isoformat(),
        }

# NOTIFICACIONES

class NotificationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        print(f"[WS NOTIF CONNECT] user_id={getattr(user, 'id', None)} anon={user.is_anonymous}")
        if not user or user.is_anonymous:
            # Close with explicit unauthorized code
            await self.close(code=4401)
            return

        self.group_name = f"user_{user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        print(f"[WS NOTIF JOIN] {self.group_name} -> {self.channel_name}")
        await self.accept()

    async def notify(self, event):
        await self.send_json({
            "type": event.get("event", "notification"),
            "payload": event.get("payload", {}),
        })
