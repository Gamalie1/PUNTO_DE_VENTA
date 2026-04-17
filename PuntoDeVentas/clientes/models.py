from django.db import models

# Create your models here.
from django.db import models

class Cliente(models.Model):
    nombre = models.CharField(max_length=150)
    direccion = models.TextField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True,)
    email = models.EmailField(blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre
