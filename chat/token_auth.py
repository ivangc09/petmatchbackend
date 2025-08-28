from urllib.parse import parse_qs
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication

class TokenAuthMiddleware(BaseMiddleware):
    """
    Lee ?token=<JWT> del query string y autentica al user.
    Si no hay token, deja el user que ya venía (por si usas cookies).
    """
    def __init__(self, inner):
        super().__init__(inner)
        self.jwt_auth = JWTAuthentication()

    async def __call__(self, scope, receive, send):
        # Mantén el usuario que dejó AuthMiddlewareStack (si lo hay)
        user = scope.get("user", AnonymousUser())

        # Extrae ?token=...
        query_string = scope.get("query_string", b"").decode()
        token = parse_qs(query_string).get("token", [None])[0]

        if token:
            user = await self._get_user_from_token(token)

        scope["user"] = user
        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def _get_user_from_token(self, raw_token):
        try:
            validated = self.jwt_auth.get_validated_token(raw_token)
            return self.jwt_auth.get_user(validated)
        except Exception:
            return AnonymousUser()