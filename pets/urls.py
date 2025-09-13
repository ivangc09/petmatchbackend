from django.urls import path
from .views import (CrearMascotaView, ListarMascotasView, ListarTodasMascotasView, 
                    CrearComentarioView, ListarComentariosView, UploadFormularioView, 
                    ListarSolicitudesAdopcionView,MostrarMascotaView,EliminarMascotaView,
                    ActualizarMascotaView, AceptarSolicitudView, RechazarSolicitudView)

urlpatterns = [
    path('crear/', CrearMascotaView.as_view(), name='crear_mascota'),
    path('mis-mascotas/', ListarMascotasView.as_view(), name='listar_mascotas'),
    path('ver-mascotas/', ListarTodasMascotasView.as_view(), name='listar_todas_mascotas'),
    path('comentarios/crear/', CrearComentarioView.as_view(), name='crear_comentario'),
    path('comentarios/<int:mascota_id>/', ListarComentariosView.as_view(), name='listar_comentarios'),
    path('solicitudes/upload/', UploadFormularioView.as_view(), name='upload_formulario'),
    path('solicitudes/mis-solicitudes/', ListarSolicitudesAdopcionView.as_view(), name='listar_solicitudes_adopcion'),
    path('detalles/<int:pk>/', MostrarMascotaView.as_view(), name='mostrar_mascota'),
    path('<int:pk>/eliminar/', EliminarMascotaView.as_view(), name='eliminar_mascota'),
    path('<int:pk>/editar/', ActualizarMascotaView.as_view(), name='actualizar_mascota'),
    path('adopciones/solicitudes/<int:pk>/aceptar/', AceptarSolicitudView.as_view(), name='aceptar_solicitud'),
    path('adopciones/solicitudes/<int:pk>/rechazar/',RechazarSolicitudView.as_view(), name="rechazar_solicitud"),
]