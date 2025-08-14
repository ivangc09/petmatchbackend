from .models import Pet, Coment, AdoptionRequest
from .serializers import PetSerializer, ComentSerializer, AdoptionRequestSerializer

from django.conf import settings
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

import json
import boto3, uuid
from botocore.exceptions import BotoCoreError, ClientError

class CrearMascotaView(generics.CreateAPIView):
    serializer_class = PetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(responsable=self.request.user)

class ListarMascotasView(generics.ListAPIView):
    serializer_class = PetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Pet.objects.filter(responsable=self.request.user)
    
class ListarTodasMascotasView(generics.ListAPIView):
    serializer_class = PetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.tipo_usuario == 'adoptante':
            return Pet.objects.filter(estado='disponible')
        
        return Pet.objects.none()
    
class CrearComentarioView(generics.CreateAPIView):
    serializer_class = ComentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(autor=self.request.user)

class ListarComentariosView(generics.ListAPIView):
    serializer_class = ComentSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        mascota_id = self.kwargs['mascota_id']
        return Coment.objects.filter(mascota_id=mascota_id).order_by('-fecha_creacion')
    

ALLOWED_CONTENT_TYPES = {
    "application/pdf", "image/jpeg", "image/png", "image/webp",
}
MAX_FILE_MB = 10

def _validate_file(f):
    if not f:
        return "Archivo faltante."
    if f.content_type not in ALLOWED_CONTENT_TYPES:
        return f"Tipo no permitido: {f.content_type}"
    if f.size > MAX_FILE_MB * 1024 * 1024:
        return f"Archivo muy grande (máx {MAX_FILE_MB} MB)."
    return None

def _to_bool(value):
    """Normaliza Sí/No/true/false/1/0 a bool (o None si no aplica)."""
    if value is None:
        return None
    s = str(value).strip().lower()
    if s in {"si", "sí", "true", "1", "yes"}:
        return True
    if s in {"no", "false", "0"}:
        return False
    return None

class UploadFormularioView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        # 1) payload
        try:
            payload = json.loads(request.data.get("payload", "{}"))
        except json.JSONDecodeError:
            return Response({"error": "payload inválido"}, status=status.HTTP_400_BAD_REQUEST)

        # 2) id de mascota (acepta varias claves)
        pet_id = request.data.get("petId") or request.data.get("mascota_id") or payload.get("mascotaID")
        if not pet_id:
            return Response({"error": "Falta el id de la mascota"}, status=status.HTTP_400_BAD_REQUEST)

        # 3) mascota
        try:
            mascota = Pet.objects.get(id=pet_id)
        except Pet.DoesNotExist:
            return Response({"error": "Mascota no encontrada"}, status=status.HTTP_404_NOT_FOUND)

        # 4) archivos (hazlos opcionales u obligatorios según tu lógica)
        id_oficial = request.FILES.get("id_oficial")
        comprobante = request.FILES.get("comprobante_domicilio")

        # si son obligatorios, valida:
        for f, fieldname in [(id_oficial, "id_oficial"), (comprobante, "comprobante_domicilio")]:
            err = _validate_file(f)
            if err:
                return Response({"error": f"{fieldname}: {err}"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            edad = int(payload.get("edad", 0) or 0)
        except ValueError:
            return Response({"error": "Edad inválida"}, status=status.HTTP_400_BAD_REQUEST)

        data = {
            "nombre": payload.get("nombre", "").strip(),
            "edad": edad,
            "ocupacion": (payload.get("ocupacion") or "").strip(),
            "estado_civil": (payload.get("estadoCivil") or "").strip(),
            "direccion": payload.get("direccion", "").strip(),
            "telefono": payload.get("telefono", "").strip(),
            "email": (payload.get("email") or "").strip(),

            "vivienda": (payload.get("vivienda") or "").strip(),
            "protegida": (_to_bool(payload.get("protegida")) is True),
            "es_propia": (_to_bool(payload.get("esPropia")) is True),

            # "No aplica" -> None
            "renta_permite": _to_bool(payload.get("rentaPermite")),

            "horas_solo": (payload.get("horasSolo") or "").strip(),
            "ejercicio": (payload.get("ejercicio") or "").strip(),

            "tuvo_mascotas": _to_bool(payload.get("tuvoMascotas")),
            "mascotas_actuales": (payload.get("mascotasActuales") or "").strip(),
            "motivo": payload.get("motivo", "").strip(),

            "responsable": (payload.get("responsable") or "").strip(),
            "familia_de_acuerdo": (_to_bool(payload.get("familiaDeAcuerdo")) is True),
            "compromiso_vida": (_to_bool(payload.get("compromisoVida")) is True),
        }

        required = [
            "nombre", "edad", "direccion", "telefono", "email",
            "vivienda", "horas_solo", "ejercicio", "motivo",
            "responsable",
        ]
        missing = [k for k in required if not data[k]]
        if missing:
            return Response({"error": f"Campos faltantes: {', '.join(missing)}"}, status=status.HTTP_400_BAD_REQUEST)
        if data["edad"] < 18:
            return Response({"error": "Edad mínima 18."}, status=status.HTTP_400_BAD_REQUEST)

        req = AdoptionRequest.objects.create(
            mascota=mascota,
            adoptante=request.user,
            **data
        )
        if id_oficial:
            req.id_oficial = id_oficial
        if comprobante:
            req.comprobante_domicilio = comprobante
        req.save()

        return Response({"ok": True,}, status=status.HTTP_201_CREATED)

class ListarSolicitudesAdopcionView(generics.ListAPIView):
    serializer_class = AdoptionRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = AdoptionRequest.objects.filter(mascota__responsable=user).order_by('-fecha_solicitud')
        mascota_id = self.request.query_params.get('mascota')

        if mascota_id:
            queryset = queryset.filter(mascota_id=mascota_id)
            
        return queryset
    
class MostrarMascotaView(generics.RetrieveAPIView):
    queryset = Pet.objects.all()
    serializer_class = PetSerializer
    permission_classes = [permissions.AllowAny]
