from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Message

User = get_user_model()

class PeerSerializer(serializers.ModelSerializer):
    nombre = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "nombre", "avatar")

    def get_nombre(self, obj):
        # Ajusta a tus campos reales (first_name/last_name/username)
        full = f"{getattr(obj, 'first_name', '')} {getattr(obj, 'last_name', '')}".strip()
        return full or getattr(obj, "username", f"Usuario {obj.id}")

    def get_avatar(self, obj):
        # Ajusta si tienes campo foto/avatar en tu modelo
        return getattr(obj, "avatar", None)

class MessageOutSerializer(serializers.ModelSerializer):
    # Renombrar campos al JSON que consume el front
    text = serializers.CharField(source="content")
    created_at = serializers.DateTimeField(source="timestamp")
    sender_id = serializers.IntegerField(read_only=True)
    recipient = serializers.IntegerField(source="receiver_id")

    class Meta:
        model = Message
        fields = ("id", "sender_id", "recipient", "text", "created_at", "read_at")
