from django.urls import path
from .views import CustomRegisterView, CustomLoginView, PerfilUsuarioView

urlpatterns = [
    path('registration/', CustomRegisterView.as_view(), name='custom_register'),
    path('custom-login/', CustomLoginView.as_view(), name='custom_login'),
    path('mi-perfil/', PerfilUsuarioView.as_view(), name='mi_perfil'),
]