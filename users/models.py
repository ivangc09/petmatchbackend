from django.db import models
from django.contrib.auth.models import AbstractUser
from .custom_storages import NoHeadObjectS3Boto3Storage

class CustomUser(AbstractUser):
    TIPO_USUARIO = (
        ('adoptante', 'Adoptante'),
        ('veterinario', 'Veterinario/Albergue'),
    )

    tipo_usuario = models.CharField(max_length=20, choices=TIPO_USUARIO, default='adoptante')
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    foto_perfil = models.ImageField(storage=NoHeadObjectS3Boto3Storage(),upload_to='fotos-perfil/', blank=True, null=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    mascotas_adoptadas = models.IntegerField(default=0, blank=True, null=True)
    mascotas_publicadas = models.IntegerField(default=0, blank=True, null=True)
    