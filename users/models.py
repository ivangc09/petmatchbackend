from django.db import models
from django.contrib.auth.models import AbstractUser

# !Añadir más datos como telefono, dirección, etc. según sea necesario

class CustomUser(AbstractUser):
    TIPO_USUARIO = (
        ('adoptante', 'Adoptante'),
        ('veterinario', 'Veterinario/Albergue'),
    )

    tipo_usuario = models.CharField(max_length=20, choices=TIPO_USUARIO, default='adoptante')