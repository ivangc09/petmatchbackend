from django.urls import path
from .views import CrearMascotaView, ListarMascotasView, ListarTodasMascotasView, CrearComentarioView, ListarComentariosView, UploadFormularioView, ListarSolicitudesAdopcionView

urlpatterns = [
    path('crear/', CrearMascotaView.as_view(), name='crear_mascota'),
    path('mis-mascotas/', ListarMascotasView.as_view(), name='listar_mascotas'),
    path('ver-mascotas/', ListarTodasMascotasView.as_view(), name='listar_todas_mascotas'),
    path('comentarios/crear/', CrearComentarioView.as_view(), name='crear_comentario'),
    path('comentarios/<int:mascota_id>/', ListarComentariosView.as_view(), name='listar_comentarios'),
    path('solicitudes/upload/', UploadFormularioView.as_view(), name='upload_formulario'),
    path('solicitudes/mis-solicitudes/', ListarSolicitudesAdopcionView.as_view(), name='listar_solicitudes_adopcion'),
]