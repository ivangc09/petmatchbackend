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
        return data

    def save(self, request):
        user = super().save(request)
        user.tipo_usuario = self.validated_data.get('tipo_usuario', 'adoptante')
        user.save()
        print("💾 Usuario guardado con tipo_usuario:", user.tipo_usuario)
        return user
    
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'tipo_usuario']
        read_only_fields = ['id', 'email', 'tipo_usuario']

