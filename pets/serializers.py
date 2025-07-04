from rest_framework import serializers
from .models import Pet, Coment, AdoptionRequest

class PetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pet
        fields = '__all__'
        read_only_fields = ['responsable']

class ComentSerializer(serializers.ModelSerializer):
    autor_username = serializers.ReadOnlyField(source='autor.username')
    
    class Meta:
        model = Coment
        fields = ['id', 'autor_username', 'mascota', 'texto', 'fecha_creacion']
        read_only_fields = ['autor', 'fecha_creacion']

class AdoptionRequestSerializer(serializers.ModelSerializer):
    mascota_nombre = serializers.ReadOnlyField(source='mascota.nombre')
    nombre_adoptante = serializers.ReadOnlyField(source='adoptante.username')

    class Meta:
        model = AdoptionRequest
        fields = ['id', 'mascota', 'mascota_nombre', 'adoptante', 'nombre_adoptante', 'url_formulario', 'fecha_solicitud']
        read_only_fields = ['url_documento','fecha_solicitud']