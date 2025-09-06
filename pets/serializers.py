from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Pet, Coment, AdoptionRequest

User = get_user_model()

class PetSerializer(serializers.ModelSerializer):
    ciudad = serializers.SerializerMethodField()
    class Meta:
        model = Pet
        fields = '__all__'
        read_only_fields = ['responsable','activo']

    def get_ciudad(self, obj):
        return obj.ciudad

class DeletePetSerializer(serializers.ModelSerializer):
    ciudad = serializers.SerializerMethodField()
    class Meta:
        model = Pet
        fields = '__all__'
        read_only_fields = ['responsable']

    def get_ciudad(self, obj):
        return obj.ciudad

class UpdatePetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pet
        fields = ['nombre', 'fotos', 'especie', 'raza', 'edad', 'tamaño', 'sexo', 'descripcion', 'estado', 'activo']
        read_only_fields = ['responsable', 'activo']

    def validate(self, attrs):
        if "edad" in attrs and attrs["edad"] < 0:
            raise serializers.ValidationError({"edad": "La edad no puede ser negativa."})
        elif "edad" in attrs and attrs["edad"] > 20:
            raise serializers.ValidationError({"edad": "Escribe una edad mas realista."})
        return attrs

class ComentSerializer(serializers.ModelSerializer):
    autor_username = serializers.ReadOnlyField(source='autor.username')
    
    class Meta:
        model = Coment
        fields = ['id', 'autor_username', 'mascota', 'texto', 'fecha_creacion']
        read_only_fields = ['autor', 'fecha_creacion']

class AdoptanteMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email"]

class AdoptionRequestListSerializer(serializers.ModelSerializer):
    adoptante = AdoptanteMiniSerializer(read_only=True)
    mascota_nombre = serializers.SerializerMethodField()
    id_oficial_url = serializers.SerializerMethodField()
    comprobante_domicilio_url = serializers.SerializerMethodField()

    class Meta:
        model = AdoptionRequest
        fields = [
            "id", "fecha_solicitud",
            "mascota", "mascota_nombre",
            "adoptante",
            "nombre", "edad", "ocupacion", "estado_civil", "direccion",
            "telefono", "email",
            "vivienda", "protegida", "es_propia", "renta_permite",
            "horas_solo", "ejercicio",
            "tuvo_mascotas", "mascotas_actuales", "motivo",
            "responsable", "familia_de_acuerdo", "compromiso_vida",
            "id_oficial_url", "comprobante_domicilio_url",
        ]
        read_only_fields = ["fecha_solicitud"]

    def get_mascota_nombre(self, obj):
        return getattr(obj.mascota, "nombre", str(obj.mascota))

    def _build_abs_url(self, request, field_file):
        if not field_file:
            return None
        try:
            url = field_file.url 
        except Exception:
            return None
        if request:
            return request.build_absolute_uri(url)
        return url

    def get_id_oficial_url(self, obj):
        request = self.context.get("request")
        return self._build_abs_url(request, obj.id_oficial)

    def get_comprobante_domicilio_url(self, obj):
        request = self.context.get("request")
        return self._build_abs_url(request, obj.comprobante_domicilio)