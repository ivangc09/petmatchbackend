# petmatchbackend/asgi.py
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "petmatchbackend.settings")

from django.core.asgi import get_asgi_application
django_asgi_app = get_asgi_application() 

from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from chat.token_auth import TokenAuthMiddleware  # importa DESPUÉS de get_asgi_application
from chat.consumers import DMConsumer            # idem

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": TokenAuthMiddleware(
        URLRouter([
            path("ws/chat/u/<int:peer_id>/", DMConsumer.as_asgi()),
        ])
    ),
})
