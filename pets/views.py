from .models import Pet, Coment, AdoptionRequest
from .serializers import (PetSerializer, ComentSerializer, AdoptionRequestListSerializer, 
                        UpdatePetSerializer,DeletePetSerializer)

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status, parsers, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q,F
from django.db import transaction
from django.shortcuts import get_object_or_404

import json
import boto3, uuid
from botocore.exceptions import BotoCoreError, ClientError
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

User = get_user_model()

#
# PAGINACION
#
class SmallPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"

class CrearMascotaView(generics.CreateAPIView):
    serializer_class = PetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(responsable=self.request.user)

class ListarMascotasView(generics.ListAPIView):
    serializer_class = PetSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["especie", "tamaño", "sexo", "estado"]
    search_fields = ["nombre", "raza"]
    ordering_fields = ["id", "nombre", "edad", "raza", "estado", "especie", "tamaño"]
    ordering = ["-id"]

    def get_queryset(self):
        return Pet.objects.filter(responsable=self.request.user,activo=True)
    
class ListarTodasMascotasView(generics.ListAPIView):
    queryset = Pet.objects.filter(activo=True,estado__in=["disponible", "urgente"]).order_by("-id")
    serializer_class = PetSerializer
    pagination_class = SmallPagination
    permission_classes = [permissions.IsAuthenticated] 
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["especie", "tamaño", "sexo", "estado"]
    search_fields = ["nombre", "raza"]
    
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
    
    
class MostrarMascotaView(generics.RetrieveAPIView):
    queryset = Pet.objects.all()
    serializer_class = DeletePetSerializer
    permission_classes = [permissions.AllowAny]

class EliminarMascotaView(generics.DestroyAPIView):
    queryset = Pet.objects.all()
    serializer_class = PetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_destroy(self, instance):
        instance.activo = False
        instance.save()

class ActualizarMascotaView(generics.RetrieveUpdateAPIView):
    serializer_class = UpdatePetSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.JSONParser, parsers.FormParser, parsers.MultiPartParser]

    def get_queryset(self):
        return Pet.objects.filter(activo=True, responsable=self.request.user)
    
# SOLICITUDES DE ADOPCION    
    
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
    pagination_class = SmallPagination
    serializer_class = AdoptionRequestListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = (
            AdoptionRequest.objects
            .select_related("mascota", "adoptante")
            .filter(mascota__responsable=user,estado="pendiente")
            .order_by("-fecha_solicitud")
        )

        pet_id = self.request.query_params.get("pet_id")
        if pet_id:
            qs = qs.filter(mascota_id=pet_id)

        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(nombre__icontains=search) |
                Q(email__icontains=search) |
                Q(telefono__icontains=search)
            )
        return qs

class RecuperarSolicitudAdopcionView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AdoptionRequestListSerializer

    def get_queryset(self):
        user = self.request.user
        return (
            AdoptionRequest.objects
            .select_related("mascota", "adoptante")
            .filter(Q(mascota__responsable=user) | Q(adoptante=user))
        )


def send_notification(user_id: int, payload: dict, event: str = "notification"):
    group = f"user_{user_id}"
    layer = get_channel_layer()

    def _send():
        if not layer:
            return
        async_to_sync(layer.group_send)(
            group,
            {"type": "notify", "event": event, "payload": payload},
        )

    transaction.on_commit(_send)

class AceptarSolicitudView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk):
        solicitud = (
            AdoptionRequest.objects
            .select_related("mascota", "adoptante")
            .select_for_update()
            .filter(pk=pk)
            .first()
        )
        if not solicitud:
            return Response({"error": "No encontrado"}, status=status.HTTP_404_NOT_FOUND)

        mascota = solicitud.mascota

        if mascota.responsable != request.user:
            return Response({"error": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)
        
        if solicitud.estado != "pendiente":
            return Response({"error": "La solicitud no está pendiente"}, status=status.HTTP_400_BAD_REQUEST)

        if mascota.estado == "adoptado":
            return Response({"error": "La mascota ya fue adoptada"}, status=status.HTTP_409_CONFLICT)
        
        mascota.estado = "adoptado"
        mascota.save(update_fields=["estado"])

        solicitud.estado = "aprobada"
        solicitud.save(update_fields=["estado"])

        (AdoptionRequest.objects
            .filter(mascota_id=mascota.id, estado="pendiente")
            .exclude(pk=solicitud.pk)
            .update(estado="rechazada"))
        
        User.objects.filter(pk=solicitud.adoptante_id).update(
            mascotas_adoptadas=F("mascotas_adoptadas") + 1
        )

        send_notification(
            solicitud.adoptante_id,
            {
                "solicitud_id": solicitud.id,
                "mascota_id": mascota.id,
                "mascota_nombre": getattr(mascota, "nombre", str(mascota.id)),
                "mensaje": f"¡Tu solicitud fue aceptada! {getattr(mascota, 'nombre','Mascota')}",
            },
            event="adoption.accepted",
        )

        return Response({
            "ok": True,
            "mascota_id": mascota.id,
            "mascota_estado": mascota.estado,
            "solicitud_id": solicitud.id,
            "solicitud_estado": solicitud.estado,
        })

class RechazarSolicitudView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self,request,pk):
        solicitud = get_object_or_404(
            AdoptionRequest.objects.select_related("mascota","adoptante"), pk=pk
        )

        mascota = solicitud.mascota

        if mascota.responsable != request.user:
            return Response({"error": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        if getattr(solicitud, "estado", "pendiente") != "pendiente":
            return Response(
                {"detail": f"No se puede rechazar: estado actual = {solicitud.estado}"},
                status=status.HTTP_409_CONFLICT,
            )
        
        solicitud.estado = "rechazada"
        solicitud.save(update_fields=["estado"])

        send_notification(
            solicitud.adoptante_id,
            {
                "solicitud_id": solicitud.id,
                "mascota_id": mascota.id,
                "mascota_nombre": getattr(mascota, "nombre", str(mascota.id)),
                "mensaje": f"¡Tu solicitud fue rechazada! {getattr(mascota, 'nombre','Mascota')}",
            },
            event="adoption.rejected",
        )

        return Response(
            {
                "id": solicitud.id,
                "estado": solicitud.estado,
                "mascota_id": mascota.id,
                "mascota_nombre": mascota.nombre,
            },
            status=status.HTTP_200_OK,
        )

class ContarMascotasView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self,request):
        u = request.user

        total_registradas = Pet.objects.filter(responsable=u,activo=True).count()

        return Response({
            "total_registradas": total_registradas
        })

#class RecomendarMascotaView(APIView):
#    permission_classes = [permissions.IsAuthenticated]
#
#    def post(self, request):
#        preferencias = request.data.get("preferencias", {})
#        mascotas = list(Pet.objects.all().values())
#
#        if not mascotas:
#            return Response(
#                {"mensaje": "No hay mascotas registradas"},
#                status=status.HTTP_404_NOT_FOUND,
#            )
#
#        prompt = f"""
#            El usuario busca una mascota con estas preferencias:
#            {preferencias}
#            
#            Estas son las mascotas disponibles:
#            {mascotas}
#            
#            Recomienda las 3 mejores opciones y explica brevemente por qué.
#            """
#
#        try:
#            openai.api_key = os.getenv("OPENAI_API_KEY")
#            respuesta = openai.ChatCompletion.create(
#                model="gpt-4o-mini",
#                messages=[{"role": "user", "content": prompt}],
#            )
#
#            return Response(
#                {"recomendaciones": respuesta.choices[0].message["content"]}
#            )
#
#        except Exception as e:
#            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#class GuardarEncuestaView(APIView):
#    permission_classes = [permissions.IsAuthenticated]
#
#    def post(self, request):
#        datos = request.data
#        # Ejemplo: guardar encuesta en tu modelo
#        # Encuesta.objects.create(usuario=request.user, **datos)
#
#        return Response(
#            {"mensaje": "Encuesta guardada correctamente"}, status=status.HTTP_200_OK
#        )


