from django.db import models
from django.conf import settings
from .custom_storages import NoHeadObjectS3Boto3Storage

class Pet(models.Model):
    ESPECIES = [('perro', 'Perro'), ('gato', 'Gato')]
    TAMANIOS = [('pequeño', 'Pequeño'), ('mediano', 'Mediano'), ('grande', 'Grande')]
    SEXOS = [('macho', 'Macho'), ('hembra', 'Hembra')]
    ESTADOS = [('disponible', 'Disponible'), ('adoptado', 'Adoptado')]

    nombre = models.CharField(max_length=100)
    fotos = models.ImageField(storage=NoHeadObjectS3Boto3Storage(),upload_to='mascotas/', blank=True, null=True)
    especie = models.CharField(max_length=10, choices=ESPECIES)
    raza = models.CharField(max_length=100)
    edad = models.IntegerField()
    tamaño = models.CharField(max_length=10, choices=TAMANIOS)
    sexo = models.CharField(max_length=10, choices=SEXOS)
    descripcion = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='disponible')
    responsable = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="mascotas")

    def __str__(self):
        return self.nombre
    
class Coment(models.Model):
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    mascota = models.ForeignKey('Pet', on_delete=models.CASCADE, related_name='comentarios')
    texto = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.autor.username} - {self.texto[:30]} \n {self.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S')}"
    
class AdoptionRequest(models.Model):
    mascota = models.ForeignKey(Pet, on_delete=models.CASCADE)
    adoptante = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='solicitudes')
    url_formulario = models.URLField()
    fecha_solicitud = models.DateTimeField(auto_now_add=True)