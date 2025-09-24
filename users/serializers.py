from dj_rest_auth.registration.serializers import RegisterSerializer
from rest_framework import serializers
from django.contrib.auth import get_user_model
import logging

User  = get_user_model()
log = logging.getLogger(__name__)

class CustomRegisterSerializer(RegisterSerializer):
    tipo_usuario = serializers.ChoiceField(
        choices=[('adoptante', 'Adoptante'),('veterinario', 'Veterinario/Albergue')],
        required=False,
        default='adoptante'
    )

    def save(self, request):
        user = super().save(request)
        tu  = self.validated_data.get('tipo_usuario', 'adoptante')
        cd  = self.validated_data.get('ciudad', '')
        tel = self.validated_data.get('telefono', '')

        log.warning(f">>>>> SAVE LLAMADO ({user.pk=}) {tu=} {cd=} {tel=}")
        user.tipo_usuario = tu
        user.ciudad = cd
        user.telefono = tel
        user.save()
        return user

    def custom_signup(self, request, user):
        tu  = self.validated_data.get('tipo_usuario', 'adoptante')
        cd  = self.validated_data.get('ciudad', '')
        tel = self.validated_data.get('telefono', '')
        log.warning(f">>>>> CUSTOM_SIGNUP LLAMADO ({user.pk=}) {tu=} {cd=} {tel=}")
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

