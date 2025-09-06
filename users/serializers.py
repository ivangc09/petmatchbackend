from dj_rest_auth.registration.serializers import RegisterSerializer
from rest_framework import serializers
from django.contrib.auth import get_user_model

User  = get_user_model()

class CustomRegisterSerializer(RegisterSerializer):
    tipo_usuario = serializers.ChoiceField(choices=[
        ('adoptante', 'Adoptante'),
        ('veterinario', 'Veterinario/Albergue')
    ])

    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        data['tipo_usuario'] = self.validated_data.get('tipo_usuario', 'adoptante')
        data['ciudad'] = self.validated_data.get('ciudad', '')
        data['telefono'] = self.validated_data.get('telefono', '')
        return data

    def save(self, request):
        user = super().save(request)
        user.tipo_usuario = self.validated_data.get('tipo_usuario', 'adoptante')
        user.ciudad = self.validated_data.get('ciudad', '')
        user.telefono = self.validated_data.get('telefono', '')
        user.save()

        return user
    
class ProfileSerializer(serializers.ModelSerializer):
    foto_perfil = serializers.ImageField(required=False)
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'tipo_usuario','ciudad', 'telefono', 'foto_perfil',
            'mascotas_adoptadas', 'mascotas_publicadas',]
        read_only_fields = ['id', 'email', 'tipo_usuario']

