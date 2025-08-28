from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/chat/u/(?P<other_user_id>\d+)/$", consumers.DMConsumer.as_asgi()),
]