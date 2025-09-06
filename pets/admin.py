from django.contrib import admin
from .models import Pet

@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'especie', 'raza', 'edad', 'tamaño', 'sexo', 'responsable','fotos','estado','activo')
    search_fields = ('nombre', 'raza')
    list_filter = ('especie', 'tamaño', 'sexo')
