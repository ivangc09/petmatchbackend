from urllib.parse import parse_qs
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication

class TokenAuthMiddleware(BaseMiddleware):
    def __init__(self, inner):
        super().__init__(inner)
        self.jwt_auth = JWTAuthentication()

    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode()
        token = parse_qs(query_string).get("token", [None])[0]
        path = scope.get("path", "")
        user = AnonymousUser()

        if token:
            parts = str(token).split()
            raw_token = parts[-1] if len(parts) > 1 else token
            user = await self._get_user_from_token(raw_token)
            uid = getattr(user, "id", None)
            print(f"[WS MIDDLEWARE] path={path} token_len={len(raw_token)} user_id={uid}")
        else:
            print(f"[WS MIDDLEWARE] path={path} SIN token")

        scope["user"] = user
        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def _get_user_from_token(self, raw_token):
        try:
            validated = self.jwt_auth.get_validated_token(raw_token)
            return self.jwt_auth.get_user(validated)
        except Exception as e:
            print("[WS MIDDLEWARE] invalid token:", e)
            return AnonymousUser()