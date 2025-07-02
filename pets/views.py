from rest_framework import generics, permissions, status
from .models import Pet, Coment, AdoptionRequest
from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
from .serializers import PetSerializer, ComentSerializer, AdoptionRequestSerializer
import boto3, uuid

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
    
class UploadFormularioView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        documento = request.FILES.get('documento')
        mascota_id = request.data.get('mascota_id')
        
        if not documento or not mascota_id:
            return Response({'error': 'Faltan datos'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            mascota = Pet.objects.get(id=mascota_id)
        except Pet.DoesNotExist:
            return Response({'error': 'Mascota no encontrada'}, status=status.HTTP_404_NOT_FOUND)

        s3 = boto3.client('s3')

        nombre_archivo = f"solicitudes/{uuid.uuid4()}_{documento.name}"

        s3.upload_fileobj(
            documento,
            settings.AWS_STORAGE_BUCKET_NAME,
            nombre_archivo,
            ExtraArgs={'ContentType': documento.content_type}
        )

        url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{nombre_archivo}"

        # Guardar la solicitud en la base
        AdoptionRequest.objects.create(
            mascota=mascota,
            adoptante=request.user,
            url_formulario=url
        )


        return Response({'mensaje': 'Solicitud registrada y documento subido', 'url': url}, status=status.HTTP_201_CREATED)
    
class ListarSolicitudesAdopcionView(generics.ListAPIView):
    serializer_class = AdoptionRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AdoptionRequest.objects.filter(mascota__responsable=self.request.user).order_by('-fecha_solicitud')
    
