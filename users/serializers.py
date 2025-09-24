from dj_rest_auth.registration.serializers import RegisterSerializer
from rest_framework import serializers
from django.contrib.auth import get_user_model
import logging

User  = get_user_model()
log = logging.getLogger(__name__)

def _grab(serializer, request, key, default=""):
    return (
        serializer.validated_data.get(key, None)
        if hasattr(serializer, "validated_data") else None
    ) or (
        serializer.initial_data.get(key, None)
        if hasattr(serializer, "initial_data") and isinstance(serializer.initial_data, dict) else None
    ) or (
        request.data.get(key, None)
        if request is not None and hasattr(request, "data") else None
    ) or default

class CustomRegisterSerializer(RegisterSerializer):
    tipo_usuario = serializers.ChoiceField(
        choices=[('adoptante', 'Adoptante'),('veterinario', 'Veterinario/Albergue')],
        required=False,
        default='adoptante'
    )
    ###

    def validate(self, attrs):
        log.warning(f">>>>> VALIDATE attrs={attrs}")
        return super().validate(attrs)

    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        data["tipo_usuario"] = self.validated_data.get("tipo_usuario", "adoptante")
        data["ciudad"] = self.validated_data.get("ciudad", "")
        data["telefono"] = self.validated_data.get("telefono", "")
        log.warning(f">>>>> get_cleaned_data -> {data}")
        return data

    # dj-rest-auth llama esto después de crear el user
    def custom_signup(self, request, user):
        tu  = _grab(self, request, "tipo_usuario", "adoptante")
        cd  = _grab(self, request, "ciudad", "")
        tel = _grab(self, request, "telefono", "")
        log.warning(f">>>>> CUSTOM_SIGNUP ({user.pk=}) {tu=} {cd=} {tel=}")

        user.tipo_usuario = tu
        user.ciudad = cd
        user.telefono = tel
        user.save()
        return user
    
    def save(self, request):
        user = super().save(request)
        tu  = _grab(self, request, "tipo_usuario", "adoptante")
        cd  = _grab(self, request, "ciudad", "")
        tel = _grab(self, request, "telefono", "")
        log.warning(f">>>>> SAVE ({user.pk=}) {tu=} {cd=} {tel=}")

        user.tipo_usuario = tu
        user.ciudad = cd
        user.telefono = tel
        user.save()
        return user
    
class ProfileSerializer(serializers.ModelSerializer):
    foto_perfil = serializers.ImageField(required=False)
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'tipo_usuario','ciudad', 'telefono', 'foto_perfil',
            'mascotas_adoptadas', 'mascotas_publicadas',]
        read_only_fields = ['id', 'email', 'tipo_usuario']

