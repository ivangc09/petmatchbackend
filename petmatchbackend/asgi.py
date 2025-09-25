import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "petmatchbackend.settings")

from django.core.asgi import get_asgi_application
django_asgi_app = get_asgi_application() 

from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path, re_path
from chat.token_auth import TokenAuthMiddleware
from chat.consumers import DMConsumer, NotificationConsumer
from chat.debug_ws import DebugWS

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": TokenAuthMiddleware(
        URLRouter([
            path("ws/chat/u/<int:peer_id>/", DMConsumer.as_asgi()),
            path("ws/notifications/", NotificationConsumer.as_asgi()),
            re_path(r"^ws/.*$", DebugWS.as_asgi()), 
        ])
    ),
})
