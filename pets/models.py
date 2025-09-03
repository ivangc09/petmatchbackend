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

    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre
    
    @property
    def ciudad(self):
        return self.responsable.ciudad
    
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
    fecha_solicitud = models.DateTimeField(auto_now_add=True)

    # DATOS DEL FORMULARIO DE ADOPCION

    nombre = models.CharField(max_length=255,default="")
    edad = models.PositiveIntegerField(default=18)
    ocupacion = models.CharField(max_length=255,blank=True, default="")
    estado_civil = models.CharField(max_length=50,blank=True, default="")
    direccion = models.TextField(default="")
    telefono = models.CharField(max_length=20,default="")
    email = models.EmailField(default="")

    vivienda = models.CharField(max_length=50,default="")
    protegida = models.BooleanField(default=False)
    es_propia = models.BooleanField(default=False)
    renta_permite = models.BooleanField(null=True,  blank=True)
    horas_solo = models.CharField(max_length=20,default="")
    ejercicio = models.CharField(max_length=20,default="")

    tuvo_mascotas = models.BooleanField(null=True, blank=True)
    mascotas_actuales = models.TextField(blank=True, default="")
    motivo = models.TextField(default="")

    responsable = models.CharField(max_length=255,default="")
    familia_de_acuerdo = models.BooleanField(default=True)
    compromiso_vida = models.BooleanField(default=True)

    # Documentos
    id_oficial = models.FileField(storage=NoHeadObjectS3Boto3Storage(),upload_to="documentos/adopciones/ids/", blank=True, null=True)
    comprobante_domicilio = models.FileField(storage=NoHeadObjectS3Boto3Storage(),upload_to="documentos/adopciones/comprobantes/", blank=True, null=True)